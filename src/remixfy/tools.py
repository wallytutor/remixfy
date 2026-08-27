# -*- coding: utf-8 -*-

import logging

from pathlib import Path


def resolve_repo_dir(url: str, repo_dir: str | Path | None) -> Path:
    if not repo_dir:
        repo_dir = repository_name(url)

    repo_dir = resolve_dir(repo_dir)
    logging.info(f"Repository at {repo_dir}")
    return repo_dir


def resolve_output_dir(url: str, output_dir: str | Path | None) -> Path:
    if not output_dir:
        output_dir = f"{repository_name(url)}_mix"

    output_dir = resolve_dir(output_dir)
    logging.info(f"Output at {output_dir}")
    return output_dir


def resolve_dir(name: str | Path | None, base: Path | None = None) -> Path:
    if isinstance(name, str):
        name = Path(name)

    if not name.is_absolute():
        if base and base.exists():
            return base.joinpath(name)
        else:
            return Path.cwd().joinpath(name)

    return name


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
