# -*- coding: utf-8 -*-

from pathlib import Path


def repository_name(url: str) -> str:
    """ Return the repository name from the URL. """
    if not url.endswith(".git"):
        raise ValueError(f"URL must end with .git: {url}")

    if len(blocks := url.split("/")) < 2:
        raise ValueError(f"Invalid URL: {url}")

    return blocks[-1].split(".")[0]


def is_text_file(file_path: str | Path, chunk_size: int = 1024) -> bool:
    """ Return True if the file is a text file. """
    with open(file_path, "rb") as f:
        chunk = f.read(chunk_size)

    if b"\x00" in chunk:
        return False

    try:
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
