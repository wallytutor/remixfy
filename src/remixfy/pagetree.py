# -*- coding: utf-8 -*-

import collections
import logging
import re
import shutil
import sys
import time

import requests

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from ruamel.yaml import YAML

from .tools import resolve_output_dir

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
        "_pagetree_path",
        "_ignored_path",
        "_retrieved_urls",
        "_ignored_urls",
        "_visited_urls",
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
            base_dir: str | Path | None = None,
        ) -> None:
        self._url: str = url
        self._parent: str | None = parent
        self._relative_links: bool = relative_links
        self._force_write: bool = force_write
        self._max_depth: int = max_depth
        self._max_pages: int = max_pages
        self._request_delay: float | int = request_delay

        self._output_dir: Path = resolve_output_dir(
            output_dir, url=url, base=base_dir
        )
        self._pagetree_path: Path = self._output_dir / ".pagetree"
        self._ignored_path: Path = self._output_dir / ".ignored"

        self._retrieved_urls: list[str] = []
        self._ignored_urls: list[str] = []
        self._visited_urls: set[str] = set()

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

        if not rel_str or rel_str.endswith("/"):
            rel_str += "index.html"
        elif "." not in Path(rel_str).name:
            rel_str += ".html"

        clean_parts = []
        for part in Path(rel_str).parts:
            subbed = re.sub(r'[<>:"\\|?*]', '_', part)
            clean_parts.append(subbed)

        return self._output_dir.joinpath(*clean_parts)

    def _crawl_pages(self) -> None:
        """ Crawl starting from seed URL using BFS traversal. """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        queue = collections.deque([(self._url, 0)])
        self._visited_urls.add(self._url)

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) remixfy-pagetree/0.1.0"
        })

        while queue and len(self._retrieved_urls) < self._max_pages:
            current_url, depth = queue.popleft()

            if self._request_delay > 0 and len(self._retrieved_urls) > 0:
                time.sleep(self._request_delay)

            try:
                resp = session.get(current_url, timeout=15)
                if resp.status_code != 200:
                    logging.warning(
                        f"Failed to fetch {current_url} (HTTP status {resp.status_code})"
                    )
                    if current_url not in self._ignored_urls:
                        self._ignored_urls.append(current_url)
                    continue
            except Exception as err:
                logging.warning(f"Failed to fetch {current_url}: {err}")
                if current_url not in self._ignored_urls:
                    self._ignored_urls.append(current_url)
                continue

            target_file = self._url_to_path(current_url)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(resp.content)

            self._retrieved_urls.append(current_url)

            if depth >= self._max_depth:
                continue

            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.find_all("a", href=True):
                raw_href = a["href"].strip()
                if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:") or raw_href.startswith("mailto:"):
                    continue

                parsed_href = urlparse(raw_href)
                is_relative = not bool(parsed_href.scheme or parsed_href.netloc)

                if is_relative and not self._relative_links:
                    if raw_href not in self._ignored_urls and raw_href not in self._visited_urls:
                        self._ignored_urls.append(raw_href)
                    continue

                resolved_url, _ = urldefrag(urljoin(current_url, raw_href))
                parsed_target = urlparse(resolved_url)

                if parsed_target.scheme not in ("http", "https"):
                    if resolved_url not in self._ignored_urls and resolved_url not in self._visited_urls:
                        self._ignored_urls.append(resolved_url)
                    continue

                if self._parent and not resolved_url.startswith(self._parent):
                    if resolved_url not in self._ignored_urls and resolved_url not in self._visited_urls:
                        self._ignored_urls.append(resolved_url)
                    continue

                if resolved_url in self._visited_urls:
                    continue

                if depth + 1 > self._max_depth:
                    if resolved_url not in self._ignored_urls:
                        self._ignored_urls.append(resolved_url)
                    continue

                self._visited_urls.add(resolved_url)
                queue.append((resolved_url, depth + 1))

        with self._pagetree_path.open("w", encoding="utf-8") as f:
            for u in self._retrieved_urls:
                f.write(f"{u}\n")

        with self._ignored_path.open("w", encoding="utf-8") as f:
            for u in self._ignored_urls:
                f.write(f"{u}\n")

        logging.info(
            f"Created .pagetree with {len(self._retrieved_urls)} URLs at "
            f"{self._pagetree_path}"
        )
        logging.info(
            f"Created .ignored with {len(self._ignored_urls)} URLs at "
            f"{self._ignored_path}"
        )

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "PageTree":
        """ Create a PageTree instance from a YAML configuration file. """
        path = Path(config_path).resolve()
        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {path}"
            )

        yaml = YAML(typ="safe")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid YAML configuration format in {path}"
            )

        kwargs = data.get("pagetree", data)
        if not isinstance(kwargs, dict):
            raise ValueError(
                f"Invalid 'pagetree' configuration block in {path}"
            )

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
