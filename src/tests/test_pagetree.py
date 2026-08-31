# -*- coding: utf-8 -*-

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from remixfy import PageTree, RepoMixfy
from remixfy.pagetree import main as pagetree_main
from remixfy.repomixfy import main as repomixfy_main


class MockResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


def test_repomixfy_from_yaml(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "code.py").write_text("x = 1", encoding="utf-8")

    config_file = tmp_path / "config.yaml"
    yaml_content = """
repomixfy:
  url: "https://github.com/user/sample_repo.git"
  fences_map:
    .py: python
"""
    config_file.write_text(yaml_content, encoding="utf-8")

    mix = RepoMixfy.from_yaml(config_file)
    assert mix._output_dir == tmp_path / "sample_repo_mix"
    assert (tmp_path / "sample_repo_mix" / ".repomixfy").exists()


def test_pagetree_crawling(tmp_path):
    seed_url = "https://doc.cfd.direct/openfoam/user-guide-v13/contents"
    parent_url = "https://doc.cfd.direct/openfoam/user-guide-v13/"

    html_contents = (
        '<html><body>'
        '<a href="page1.html">Page 1</a>'
        '<a href="https://doc.cfd.direct/openfoam/user-guide-v13/page2.html">Page 2</a>'
        '<a href="https://external.org/about">External</a>'
        '<a href="#section">Fragment</a>'
        '<a href="mailto:info@cfd.direct">Contact</a>'
        '</body></html>'
    )
    html_page1 = '<html><body><a href="page3.html">Page 3</a></body></html>'
    html_page2 = '<html><body><h1>Page 2 Content</h1></body></html>'
    html_page3 = '<html><body><h1>Page 3 Content</h1></body></html>'

    responses_map = {
        "https://doc.cfd.direct/openfoam/user-guide-v13/contents": MockResponse(html_contents.encode("utf-8")),
        "https://doc.cfd.direct/openfoam/user-guide-v13/page1.html": MockResponse(html_page1.encode("utf-8")),
        "https://doc.cfd.direct/openfoam/user-guide-v13/page2.html": MockResponse(html_page2.encode("utf-8")),
        "https://doc.cfd.direct/openfoam/user-guide-v13/page3.html": MockResponse(html_page3.encode("utf-8")),
    }

    def mock_get(url, **kwargs):
        if url in responses_map:
            return responses_map[url]
        return MockResponse(b"Not Found", status_code=404)

    output_dir = tmp_path / "openfoam_output"
    config_file = tmp_path / "pagetree_config.yaml"
    yaml_content = f"""
pagetree:
  url: "{seed_url}"
  parent: "{parent_url}"
  relative_links: true
  output_dir: "{output_dir.as_posix()}"
  force_write: true
  max_depth: 3
  max_pages: 10
  request_delay: 0
"""
    config_file.write_text(yaml_content, encoding="utf-8")

    with patch("requests.Session.get", side_effect=mock_get):
        pagetree_main(["-c", str(config_file)])

    assert output_dir.exists()
    pagetree_file = output_dir / ".pagetree"
    ignored_file = output_dir / ".ignored"

    assert pagetree_file.exists()
    assert ignored_file.exists()

    retrieved = pagetree_file.read_text(encoding="utf-8").splitlines()
    ignored = ignored_file.read_text(encoding="utf-8").splitlines()

    assert seed_url in retrieved
    assert "https://doc.cfd.direct/openfoam/user-guide-v13/page1.html" in retrieved
    assert "https://doc.cfd.direct/openfoam/user-guide-v13/page2.html" in retrieved
    assert "https://doc.cfd.direct/openfoam/user-guide-v13/page3.html" in retrieved

    assert "https://external.org/about" in ignored

    assert (output_dir / "contents.html").exists()
    assert (output_dir / "page1.html").exists()
    assert (output_dir / "page2.html").exists()
    assert (output_dir / "page3.html").exists()


def test_pagetree_max_depth(tmp_path):
    seed_url = "http://test.local/index.html"
    parent_url = "http://test.local/"

    responses_map = {
        "http://test.local/index.html": MockResponse(b'<a href="level1.html">L1</a>'),
        "http://test.local/level1.html": MockResponse(b'<a href="level2.html">L2</a>'),
        "http://test.local/level2.html": MockResponse(b'<a href="level3.html">L3</a>'),
    }

    def mock_get(url, **kwargs):
        return responses_map.get(url, MockResponse(b"", 404))

    out_dir = tmp_path / "depth_test"

    with patch("requests.Session.get", side_effect=mock_get):
        pt = PageTree(
            url=seed_url,
            parent=parent_url,
            output_dir=out_dir,
            max_depth=1,
            request_delay=0,
            force_write=True,
        )

    retrieved = (out_dir / ".pagetree").read_text(encoding="utf-8").splitlines()
    assert "http://test.local/index.html" in retrieved
    assert "http://test.local/level1.html" in retrieved
    assert "http://test.local/level2.html" not in retrieved


def test_pagetree_html_filtering(tmp_path):
    seed_url = "http://test.local/index.html"
    parent_url = "http://test.local/"

    raw_html = (
        '<html>'
        '<head><title>Test</title><script>var x = 1;</script></head>'
        '<body>'
        '<header><h1>Header</h1></header>'
        '<main id="content"><h2>Main Content</h2><p>Hello world</p></main>'
        '<footer>Footer info</footer>'
        '</body>'
        '</html>'
    )

    def mock_get(url, **kwargs):
        return MockResponse(raw_html.encode("utf-8"))

    out_dir = tmp_path / "filter_test"

    with patch("requests.Session.get", side_effect=mock_get):
        pt = PageTree(
            url=seed_url,
            parent=parent_url,
            output_dir=out_dir,
            parent_tag={"tag_name": "main", "id": "content"},
            skip_tags=["header", "footer", "script"],
            request_delay=0,
            force_write=True,
        )

    saved_file = out_dir / "index.html"
    assert saved_file.exists()
    content = saved_file.read_text(encoding="utf-8")

    assert "Main Content" in content
    assert "Header" not in content
    assert "Footer info" not in content
    assert "var x = 1" not in content

