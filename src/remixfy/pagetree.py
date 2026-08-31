# -*- coding: utf-8 -*-

import collections
import logging
import re
import shutil
import subprocess
import sys
import time

import networkx as nx
import requests

from argparse import ArgumentParser
from pathlib import Path
from typing import Self
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

from .tools import resolve_output_dir, load_yaml

logging.basicConfig(
    stream = sys.stdout,
    level  = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)


class PageTree:
    """ Crawls and retrieves web pages based on configurations.

    Parameters
    ----------
    url : str
        Seed URL to start scraping from.
    parent : str, optional
        Parent URL string prefix under which scraped URLs must live.
    relative_links : bool, default=True
        Whether relative links should be scraped (following parent rule).
    output_dir : str, Path, or None, optional
        Destination directory path for scraped page files.
    force_write : bool, default=False
        If True, overwrite output directory if it already exists.
    max_depth : int, default=5
        Maximum recursive depth of pages to visit.
    max_pages : int, default=1000
        Maximum total number of pages to retrieve.
    request_delay : float or int, default=1
        Delay in seconds between consecutive HTTP requests.
    parent_tag : dict, optional
        Tag specification to extract specific HTML content subtree.
    skip_tags : list of str, optional
        List of HTML tag names to remove before saving content.
    convert_md : bool, default=False
        If True, convert page output to Markdown format using Pandoc.
    plain_html : bool, default=False
        If True and convert_md is False, strip all HTML attributes.
    base_dir : str, Path, or None, optional
        Base directory to resolve relative output directory against.
    """

    __slots__ = (
        "_url",
        "_parent",
        "_relative_links",
        "_output_dir",
        "_force_write",
        "_max_depth",
        "_max_pages",
        "_request_delay",
        "_parent_tag",
        "_skip_tags",
        "_convert_md",
        "_plain_html",
        "_pagetree_path",
        "_ignored_path",
        "_graph_path",
        "_retrieved_urls",
        "_ignored_urls",
        "_visited_urls",
        "_graph",
    )

    def __init__(
            self,
            url: str,
            parent: str | None = None,
            relative_links: bool = True,
            output_dir: str | Path | None = None,
            force_write: bool = False,
            max_depth: int = 5,
            max_pages: int = 1000,
            request_delay: float | int = 1,
            parent_tag: dict | None = None,
            skip_tags: list[str] | None = None,
            convert_md: bool = False,
            plain_html: bool = False,
            base_dir: str | Path | None = None,
        ) -> None:
        self._url: str = url
        self._parent: str | None = parent
        self._relative_links: bool = relative_links
        self._force_write: bool = force_write
        self._max_depth: int = max_depth
        self._max_pages: int = max_pages
        self._request_delay: float | int = request_delay
        self._parent_tag: dict | None = parent_tag
        self._skip_tags: list[str] | None = skip_tags
        self._convert_md: bool = convert_md
        self._plain_html: bool = plain_html

        self._output_dir: Path = resolve_output_dir(
            output_dir, url=url, base=base_dir
        )
        self._pagetree_path: Path = self._output_dir / ".pagetree"
        self._ignored_path: Path = self._output_dir / ".ignored"
        self._graph_path: Path = self._output_dir / "pagetree.graphml"

        self._retrieved_urls: set[str] = set()
        self._ignored_urls: set[str] = set()
        self._visited_urls: set[str] = set()
        self._graph: nx.DiGraph = nx.DiGraph()

        self._init_outputs(force_write)
        self._crawl_pages()

    def _init_outputs(self, force_write: bool) -> None:
        """ Initialize output directory state.

        Parameters
        ----------
        force_write : bool
            If True, remove existing output directory before
            proceeding; if False and output file exists, exit.
        """
        if self._pagetree_path.exists():
            if force_write:
                logging.info(
                    f"Overwriting .pagetree file at "
                    f"{self._pagetree_path} and associated files"
                )
                shutil.rmtree(self._output_dir)
            else:
                logging.info(
                    f"Skipping .pagetree file creation. Set "
                    f"force_write = True to overwrite."
                )
                sys.exit(0)

    def _url_to_path(self, url: str) -> Path:
        """ Map a URL to a sanitized relative local file path.

        Parameters
        ----------
        url : str
            URL to map.

        Returns
        -------
        Path
            Absolute path within output_dir where the page content
            should be stored.
        """
        parsed = urlparse(url)
        parent_str = self._parent or self._url

        if parent_str and url.startswith(parent_str):
            rel_str = url[len(parent_str):].lstrip("/")
        else:
            rel_str = (parsed.netloc + parsed.path).lstrip("/")

        rel_str = rel_str.split("?")[0].split("#")[0]

        ext = ".md" if self._convert_md else ".html"

        if not rel_str or rel_str.endswith("/"):
            rel_str += f"index{ext}"
        else:
            p = Path(rel_str)
            if p.suffix.lower() in (".html", ".htm"):
                rel_str = str(p.with_suffix(ext))
            elif "." not in p.name:
                rel_str += ext

        clean_parts = []
        for part in Path(rel_str).parts:
            subbed = re.sub(r'[<>:"\\|?*]', '_', part)
            clean_parts.append(subbed)

        return self._output_dir.joinpath(*clean_parts)

    def _record_retrieved(self, url: str) -> None:
        """ Write a retrieved URL to the .pagetree in append mode.

        Parameters
        ----------
        url : str
            Retrieved URL to record.
        """
        if url in self._retrieved_urls:
            logging.info(f"Skipping already retrieved URL: {url}")
            return

        self._retrieved_urls.add(url)
        with self._pagetree_path.open("a", encoding="utf-8") as f:
            f.write(f"{url}\n")

    def _record_ignored(self, url: str) -> None:
        """ Write an ignored URL to the .ignored in append mode.

        Parameters
        ----------
        url : str
            Ignored URL to record.
        """
        if url in self._ignored_urls:
            return

        self._ignored_urls.add(url)
        with self._ignored_path.open("a", encoding="utf-8") as f:
            f.write(f"{url}\n")

    def _fetch_page(
            self,
            session: requests.Session,
            current_url: str
        ) -> requests.Response | None:
        """ Fetch an HTTP resource using the current session.

        Parameters
        ----------
        session : requests.Session
            Active HTTP session instance.
        current_url : str
            Target URL to request.

        Returns
        -------
        requests.Response or None
            Response object if successful (HTTP 200), None otherwise.
        """
        try:
            resp = session.get(current_url, timeout=15)

            if resp.status_code != 200:
                logging.warning(
                    f"Failed to fetch {current_url} (HTTP status {resp.status_code})"
                )
                self._record_ignored(current_url)
                return None
            return resp
        except Exception as err:
            logging.warning(f"Failed to fetch {current_url}: {err}")
            self._record_ignored(current_url)
            return None

    def _html_to_markdown(self, html_bytes: bytes) -> bytes:
        """ Convert HTML bytes payload to Markdown format using Pandoc.

        Parameters
        ----------
        html_bytes : bytes
            HTML payload bytes to convert.

        Returns
        -------
        bytes
            Converted Markdown content bytes.
        """
        try:
            cmd = ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"]
            res = subprocess.run(
                cmd,
                input=html_bytes,
                capture_output=True,
                check=True
            )
            return res.stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as err:
            logging.warning(f"Pandoc markdown conversion failed: {err}")
            return html_bytes

    def _clean_plain_html(self, soup: BeautifulSoup) -> None:
        """ Strip attributes and remove/unwrap elements.

        It performs the following steps:
          - strip element attributes,
          - remove empty tags,
          - unwrap dangling div/span tags.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML tree to clean up.
        """
        if not hasattr(soup, "find_all"):
            return

        for tag in soup.find_all(True):
            tag.attrs = {}

        void_tags = {"img", "br", "hr", "input", "source", "wbr"}

        while True:
            removed_any = False
            for tag in soup.find_all(True):
                if tag.name not in void_tags:
                    if (
                        not tag.get_text(strip=True) and
                        not tag.find_all(void_tags)
                    ):
                        tag.decompose()
                        removed_any = True
            if not removed_any:
                break

        for tag in soup.find_all(["div", "span"]):
            tag.unwrap()


    def _filter_html(self, content: bytes) -> bytes:
        """ Filter HTML content.

        It performs the following steps:
          - stripping skip_tags,
          - extracting parent_tag,
          - optionally converting to Markdown or plain HTML.

        Parameters
        ----------
        content : bytes
            Raw response content bytes.

        Returns
        -------
        bytes
            Filtered content bytes (HTML or Markdown).
        """
        if (
            not self._parent_tag
            and not self._skip_tags
            and not self._convert_md
            and not self._plain_html
        ):
            return content

        try:
            soup = BeautifulSoup(content, "html.parser")
        except Exception as err:
            logging.warning(f"Failed to parse HTML for filtering: {err}")
            return content

        if self._skip_tags:
            for tag_name in self._skip_tags:
                if tag_name:
                    for elem in soup.find_all(tag_name):
                        elem.decompose()

        if self._parent_tag and isinstance(self._parent_tag, dict):
            tag_name = self._parent_tag.get("tag_name")
            tag_id = self._parent_tag.get("id")
            tag_class = self._parent_tag.get("class")

            kwargs = {}

            if tag_id:
                kwargs["id"] = tag_id
            if tag_class:
                kwargs["class"] = tag_class

            if tag_name:
                elem = soup.find(tag_name, **kwargs)
            elif kwargs:
                elem = soup.find(attrs=kwargs)
            else:
                elem = None

            if elem:
                soup = elem
            else:
                logging.warning(
                    f"Parent tag specification {self._parent_tag} not found"
                )

        if self._convert_md or self._plain_html:
            self._clean_plain_html(soup)

        if self._convert_md:
            html_bytes = str(soup).encode("utf-8")
            return self._html_to_markdown(html_bytes)

        return str(soup).encode("utf-8")

    def _save_page(self, current_url: str, content: bytes) -> None:
        """ Write page content to disk and record retrieved URL.

        Parameters
        ----------
        current_url : str
            URL of the page being saved.
        content : bytes
            Binary response payload to save.
        """
        self._graph.add_node(current_url)
        filtered_content = self._filter_html(content)
        target_file = self._url_to_path(current_url)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(filtered_content)
        self._record_retrieved(current_url)

    def _process_link(
            self,
            current_url: str,
            raw_href: str,
            depth: int,
            queue: collections.deque
        ) -> None:
        """ Evaluate and process a single hyperlink extracted from a page.

        Parameters
        ----------
        current_url : str
            URL of the referring page.
        raw_href : str
            Raw href attribute string from an HTML anchor tag.
        depth : int
            Current depth of the referring page.
        queue : collections.deque
            BFS URL processing queue.
        """
        raw_href = raw_href.strip()
        if (
            not raw_href
            or raw_href.startswith("#")
            or raw_href.startswith("javascript:")
            or raw_href.startswith("mailto:")
        ):
            return

        parsed_href = urlparse(raw_href)
        is_relative = not bool(parsed_href.scheme or parsed_href.netloc)

        if is_relative and not self._relative_links:
            if raw_href not in self._visited_urls:
                self._record_ignored(raw_href)
            return

        resolved_url, _ = urldefrag(urljoin(current_url, raw_href))
        parsed_target = urlparse(resolved_url)

        if parsed_target.scheme not in ("http", "https"):
            if resolved_url not in self._visited_urls:
                self._record_ignored(resolved_url)
            return

        self._graph.add_edge(current_url, resolved_url)

        if self._parent and not resolved_url.startswith(self._parent):
            if resolved_url not in self._visited_urls:
                self._record_ignored(resolved_url)
            return

        if resolved_url in self._retrieved_urls:
            logging.info(f"Skipping already retrieved URL: {resolved_url}")
            return

        if resolved_url in self._visited_urls:
            return

        if depth + 1 > self._max_depth:
            self._record_ignored(resolved_url)
            return

        self._visited_urls.add(resolved_url)
        queue.append((resolved_url, depth + 1))

    def _extract_links(
            self,
            current_url: str,
            content: bytes,
            depth: int,
            queue: collections.deque
        ) -> None:
        """ Extract all anchor links from HTML content and process them.

        Parameters
        ----------
        current_url : str
            URL of the page containing the HTML content.
        content : bytes
            Raw HTML payload.
        depth : int
            Current recursive crawling depth.
        queue : collections.deque
            BFS URL processing queue.
        """
        soup = BeautifulSoup(content, "html.parser")
        for a in soup.find_all("a", href=True):
            self._process_link(current_url, a["href"], depth, queue)

    def _dump_graph(self) -> None:
        """ Dump the networkx graph to a GraphML file. """
        nx.write_graphml(self._graph, self._graph_path)
        logging.info(
            f"Saved graph with {self._graph.number_of_nodes()} nodes and "
            f"{self._graph.number_of_edges()} edges at {self._graph_path}"
        )

    def _crawl_pages(self) -> None:
        """ Crawl starting from seed URL using BFS traversal. """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        queue = collections.deque([(self._url, 0)])
        self._visited_urls.add(self._url)

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "remixfy-pagetree/0.1.0"
            )
        })

        while queue and len(self._retrieved_urls) < self._max_pages:
            current_url, depth = queue.popleft()

            if current_url in self._retrieved_urls:
                logging.info(f"Skipping already retrieved URL: {current_url}")
                continue

            if self._request_delay > 0 and len(self._retrieved_urls) > 0:
                time.sleep(self._request_delay)

            resp = self._fetch_page(session, current_url)
            if resp is None:
                continue

            self._save_page(current_url, resp.content)

            if depth < self._max_depth:
                self._extract_links(current_url, resp.content, depth, queue)

        logging.info(
            f"Created .pagetree with {len(self._retrieved_urls)} URLs at "
            f"{self._pagetree_path}"
        )
        logging.info(
            f"Created .ignored with {len(self._ignored_urls)} URLs at "
            f"{self._ignored_path}"
        )
        self._dump_graph()

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> Self:
        """ Create a PageTree instance from a YAML configuration file. """
        path = Path(config_path).resolve()
        kwargs = load_yaml(path, "pagetree")
        return cls(**kwargs, base_dir=path.parent)


def main(cli_args: list[str] | None = None) -> None:
    """ Main entry point for the pagetree CLI. """
    parser = ArgumentParser(
        description = "Remixfy web page crawler and retriever."
    )
    parser.add_argument(
        "-c", "--config",
        required=True,
        type=str,
        help="Path to YAML configuration file"
    )
    args = parser.parse_args(cli_args)

    PageTree.from_yaml(args.config)
