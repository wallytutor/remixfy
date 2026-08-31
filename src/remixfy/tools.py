# -*- coding: utf-8 -*-

import logging
import subprocess

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ruamel.yaml import YAML


def resolve_repo_dir(
        repo_dir: str | Path | None,
        url: str | None = None,
        base: str | Path | None = None
    ) -> Path:
    """ Resolve the repository directory path.

    Parameters
    ----------
    repo_dir : str, Path, or None
        Target directory path for the repository.
    url : str, optional
        Repository URL used to infer the repository name
        if `repo_dir` is None.
    base : str, Path, or None, optional
        Base directory to resolve relative paths against.

    Returns
    -------
    Path
        Resolved path for the repository directory.

    Raises
    ------
    ValueError
        If neither `repo_dir` nor `url` is provided.
    """
    if not repo_dir and not url:
        raise ValueError("Must provide repo_dir or url")

    repo_dir = repo_dir or repository_name(url)
    repo_dir = resolve_dir(repo_dir, base=base)
    logging.info(f"Repository at {repo_dir}")
    return repo_dir


def resolve_output_dir(
        output_dir: str | Path | None,
        url: str | None = None,
        base: str | Path | None = None
    ) -> Path:
    """ Resolve the output directory path.

    Parameters
    ----------
    output_dir : str, Path, or None
        Target directory path for generated output.
    url : str, optional
        Repository URL used to infer the default output folder
        name if `output_dir` is None.
    base : str, Path, or None, optional
        Base directory to resolve relative paths against.

    Returns
    -------
    Path
        Resolved path for the output directory.

    Raises
    ------
    ValueError
        If neither `output_dir` nor `url` is provided.
    """
    if not output_dir and not url:
        raise ValueError("Must provide output_dir or url")

    if not output_dir:
        if url and url.endswith(".git"):
            output_dir = f"{repository_name(url)}_mix"
        elif url:
            domain_name = get_domain_name(url)
            output_dir = f"{domain_name}_mix"
        else:
            output_dir = "output_mix"

    output_dir = resolve_dir(output_dir, base=base)
    logging.info(f"Output at {output_dir}")
    return output_dir


def get_domain_name(url: str) -> str:
    """ Extract the domain name from a URL.

    Parameters
    ----------
    url : str
        URL string to parse.

    Returns
    -------
    str
        Sanitized domain name string.
    """
    if not (parsed := urlparse(url)).netloc:
        return "web"

    return parsed.netloc.replace(":", "_").replace(".", "_")


def resolve_dir(
        name: str | Path | None,
        base: str | Path | None = None
    ) -> Path:
    """ Resolve a directory path.

    Resolution may be relative to a base directory or
    the current working directory.

    Parameters
    ----------
    name : str, Path, or None
        Path or directory name to resolve. If None, defaults
        to current working directory.
    base : str, Path, or None, optional
        Base directory for relative path resolution.

    Returns
    -------
    Path
        Resolved Path object.
    """
    name = name or Path.cwd()
    base = base or Path.cwd()

    name = Path(name) if isinstance(name, str) else name
    base = Path(base) if isinstance(base, str) else base

    if not name.is_absolute():
        return base.joinpath(name)

    return name


def repository_name(url: str) -> str:
    """ Extract the repository name from a Git URL.

    Parameters
    ----------
    url : str
        Git repository URL (must end with '.git').

    Returns
    -------
    str
        Repository name extracted from the URL.

    Raises
    ------
    ValueError
        If `url` does not end with '.git' or is invalid.
    """
    if not url.endswith(".git"):
        raise ValueError(f"URL must end with .git: {url}")

    if len(blocks := url.split("/")) < 2:
        raise ValueError(f"Invalid URL: {url}")

    return blocks[-1].split(".")[0]


def is_text_file(
        file_path: str | Path,
        chunk_size: int = 1024
    ) -> bool:
    """ Determine whether a file is likely a text file.

    Parameters
    ----------
    file_path : str or Path
        Path to the file to inspect.
    chunk_size : int = 1024
        Number of bytes to read for text detection.

    Returns
    -------
    bool
        True if the file contains no null bytes and decodes
        as UTF-8, False otherwise.
    """
    with open(file_path, "rb") as f:
        chunk = f.read(chunk_size)

    if b"\x00" in chunk:
        return False

    try:
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def get_extensions(
        ignores: list[str] | set[str] | None,
        case_sensitive: bool
    ) -> set[str]:
    """ Normalize and filter a collection of file extension rules.

    Parameters
    ----------
    ignores : list of str, set of str, or None
        File extension strings to normalize.
    case_sensitive : bool
        If False, convert all extensions to lowercase.

    Returns
    -------
    set of str
        Normalized set of file extensions, each starting with
        a leading dot.
    """
    if ignores is None:
        return set()

    # Ensure that all extensions start with a dot.
    ignores = {e if e.startswith(".") else f".{e}" for e in ignores}

    # If case insensitive, convert all extensions to lowercase.
    if not case_sensitive:
        ignores = {e.lower() for e in ignores}

    return ignores


def clone_repository(
        url: str,
        branch: str | None = None,
        repo_dir: str | Path | None = None,
        base: str | Path | None = None
    ) -> None:
    """ Clone a remote Git repository to a target directory.

    If the target directory already exists, the repository is not cloned.

    Parameters
    ----------
    url : str
        Git repository URL to clone.
    branch : str, optional
        Git branch to check out during clone.
    repo_dir : str, Path, or None, optional
        Destination directory path for the cloned repository.
    base : str, Path, or None, optional
        Base directory to resolve `repo_dir` against.

    Raises
    ------
    subprocess.CalledProcessError
        If the `git clone` command fails.
    """
    repo_dir = resolve_repo_dir(repo_dir, url=url, base=base)

    if repo_dir.exists() and repo_dir.is_dir():
        logging.info(f"Repository already cloned at {repo_dir}")
        return

    cmd = ["git", "clone"]

    if branch:
        cmd.extend(["--branch", branch])

    cmd.append(url)

    if repo_dir:
        cmd.append(str(repo_dir))

    subprocess.run(cmd, check=True, capture_output=True)


def load_yaml(path: Path, tool: str) -> dict[str, Any]:
    """ Load a YAML configuration file for a specific tool.

    Parameters
    ----------
    path : Path
        Path to the YAML configuration file.
    tool : str
        Tool section name to load from YAML.

    Returns
    -------
    dict of str to Any
        Configuration options dictionary for the specified tool.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data = YAML(typ="safe").load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid YAML configuration format in {path}"
        )

    kwargs = data.get(tool, data)

    if not isinstance(kwargs, dict):
        raise ValueError(
            f"Invalid '{tool}' configuration block in {path}"
        )

    return kwargs

