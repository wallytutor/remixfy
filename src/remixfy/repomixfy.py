# -*- coding: utf-8 -*-

import fnmatch
import logging
import math
import os
import shutil
import sys

from pathlib import Path
from typing import Any

from .tools import (
    clone_repository,
    get_extensions,
    is_text_file,
    resolve_repo_dir,
    resolve_output_dir,
)


class RepoMixfy:
    """ Handles the processing of a single repository into output files.

    Parameters
    ----------
    url : str
        Git repository URL to clone.
    branch : str, optional
        Git branch to check out during clone.
    repo_dir : str, Path, or None, optional
        Destination directory path for the cloned repository.
    output_dir : str, Path, or None, optional
        Destination directory path for the generated output files.
    size_max : float, optional
        Maximum size of output files in MB.
    case_sensitive_ext : bool, optional
        Whether file extension matching should be case-sensitive.
    force_write : bool, optional
        Whether to allow overwriting of outputs directory.
    ignore_files : list[str], optional
        List of file names to ignore.
    ignore_dirs : list[str], optional
        List of directory names to ignore.
    ignore_ext : list[str], optional
        List of file extensions to ignore.
    fences_map : dict, optional
        Map of fences to use for chunking. Key: file extension (with
        leading dot), Value: fence name
    base_dir : str, Path, or None, optional
        Base directory for relative path resolution.
    """

    __slots__ = (
        "_url",
        "_branch",
        "_repo_dir",
        "_output_dir",
        "_ignore_files",
        "_ignore_dirs",
        "_ignore_ext",
        "_max_bytes",
        "_fences_map",
        "_repomixfy_path",
    )

    def __init__(
            self,
            url: str,
            branch: str = "main",
            repo_dir: str | Path | None = None,
            output_dir: str | Path | None = None,
            size_max: float = 2.0,
            case_sensitive_ext: bool = False,
            force_write: bool = False,
            ignore_files: list[str] | None = None,
            ignore_dirs: list[str] | None = None,
            ignore_ext: list[str] | None = None,
            fences_map: dict | None = None,
            base_dir: str | Path | None = None,
        ) -> None:
        ignore_ext = get_extensions(ignore_ext, case_sensitive_ext)

        self._url: str = url
        self._branch: str = branch
        self._repo_dir: Path = resolve_repo_dir(
            repo_dir, url=url, base=base_dir
        )
        self._output_dir: Path = resolve_output_dir(
            output_dir, url=url, base=base_dir
        )
        self._ignore_files: list[str] = ignore_files or []
        self._ignore_dirs: list[str] = ignore_dirs or []
        self._ignore_ext: set[str] = ignore_ext
        self._max_bytes: int = int(size_max * 1024 ** 2)
        self._fences_map: dict = fences_map or {}

        self._repomixfy_path: Path = self._output_dir / ".repomixfy"

        clone_repository(
            self._url,
            self._branch,
            self._repo_dir,
            base=base_dir,
        )

        self._init_outputs(force_write)
        self._init_files(case_sensitive_ext)
        self._process_files()

    def _is_dir_ignored(self, dir_parts: tuple[str, ...]) -> bool:
        """ Check if directory must be ignored.

        Parameters
        ----------
        dir_parts : tuple of str
            Path components relative to repository root.

        Returns
        -------
        bool
            True if the directory is ignored, False otherwise.
        """
        if not dir_parts or not self._ignore_dirs:
            return False

        for raw_pattern in self._ignore_dirs:
            is_anchored = (
                raw_pattern.startswith("./")
                or raw_pattern.startswith(".\\")
            )

            if is_anchored:
                raw_pat = raw_pattern[2:]
            else:
                raw_pat = raw_pattern

            pattern = raw_pat.strip("/").replace("\\", "/")

            if not pattern:
                continue

            pattern_parts = tuple(pattern.split("/"))
            n = len(pattern_parts)

            if is_anchored:
                if len(dir_parts) >= n:
                    if all(
                        s == p or fnmatch.fnmatch(s, p)
                        for s, p in zip(dir_parts[:n], pattern_parts)
                    ):
                        return True

            else:
                if len(pattern_parts) == 1:
                    pat = pattern_parts[0]

                    for part in dir_parts:
                        if part == pat or fnmatch.fnmatch(part, pat):
                            return True

                else:
                    for i in range(len(dir_parts) - n + 1):
                        slice_parts = dir_parts[i:i + n]

                        if all(
                            s == p or fnmatch.fnmatch(s, p)
                            for s, p in zip(slice_parts, pattern_parts)
                        ):
                            return True

        return False

    def _init_outputs(self, force_write: bool) -> None:
        """ Initialize output directory state.

        Parameters
        ----------
        force_write : bool
            If True, remove existing output directory before proceeding;
            if False and output file exists, exit process.
        """
        if self._repomixfy_path.exists():
            if force_write:
                logging.info(
                    f"Overwriting .repomixfy file at "
                    f"{self._repomixfy_path} and associated files"
                )
                shutil.rmtree(self._output_dir)
            else:
                logging.info(
                    f"Skipping .repomixfy file creation. Set "
                    f"force_write = True to overwrite."
                )
                sys.exit(0)

    def _init_files(self, case_sensitive_ext: bool) -> None:
        """ Scan repository files and write list of non-ignored files.

        Parameters
        ----------
        case_sensitive_ext : bool
            Whether file extension matching should be case-sensitive.

        Raises
        ------
        FileNotFoundError
            If repository directory does not exist.
        """
        if not self._repo_dir.exists():
            raise FileNotFoundError(
                f"Repository directory not found at {self._repo_dir}"
            )

        self._output_dir.mkdir(parents=True, exist_ok=True)

        file_paths: list[str] = []

        for root, dirs, files in os.walk(self._repo_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self._repo_dir)

            dirs[:] = [
                d for d in dirs
                if not self._is_dir_ignored((rel_root / d).parts)
            ]

            for file in files:

                file_path = root_path / file
                rel_path = file_path.relative_to(self._repo_dir)

                if self._is_dir_ignored(rel_path.parts[:-1]):
                    continue

                if any(
                    file == pat or fnmatch.fnmatch(file, pat)
                    for pat in self._ignore_files
                ):
                    continue

                suffix = file_path.suffix

                if not case_sensitive_ext:
                    suffix = suffix.lower()

                if suffix in self._ignore_ext:
                    continue

                file_paths.append(rel_path.as_posix())

        file_paths.sort()

        with self._repomixfy_path.open("w", encoding="utf-8") as f:
            for rel_path in file_paths:
                f.write(f"{rel_path}\n")

        logging.info(
            f"Created .repomixfy with {len(file_paths)} files at "
            f"{self._repomixfy_path}"
        )

    def _format_file_block(
            self,
            rel_str: str,
            file_path: Path,
            fence_val: Any
        ) -> str | None:
        """ Format a single source file into a markdown fenced block.

        Parameters
        ----------
        rel_str : str
            Relative file path string.
        file_path : Path
            Absolute file path.
        fence_val : str or callable
            Language string or transformer function for the file content.

        Returns
        -------
        str or None
            Formatted markdown block string, or None if reading or
            processing failed.
        """
        try:
            content = file_path.read_text(
                encoding="utf-8", errors="replace"
            )
        except Exception as err:
            logging.warning(f"Failed to read {file_path}: {err}")
            return None

        if callable(fence_val):
            try:
                processed = fence_val(content)
            except TypeError:
                processed = fence_val(content, file_path)

            if not isinstance(processed, str):
                return None

            if (
                processed.startswith("`")
                or processed.startswith("#")
                or processed.startswith("File:")
            ):
                return f"{processed}\n\n"
            else:
                return (
                    f"## File: {rel_str}\n\n"
                    f"```text\n{processed}\n```\n\n"
                )
        else:
            return (
                f"## File: {rel_str}\n\n"
                f"```{str(fence_val)}\n{content}\n```\n\n"
            )

    def _process_files(self) -> None:
        """ Process all listed files into chunked markdown files. """
        if not self._repomixfy_path.exists():
            logging.warning(
                f".repomixfy file missing at {self._repomixfy_path}"
            )
            return

        with self._repomixfy_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            return

        n_lines = len(lines)
        fmt_digits = max(1, int(math.ceil(math.log10(n_lines))))

        def output_name(current_id: int) -> Path:
            file_numb = f"{current_id:0{fmt_digits}d}"
            file_name = f"{self._repo_dir.name}-{file_numb}.md"
            return self._output_dir / file_name

        current_id = 1
        current_md_path = output_name(current_id)

        for rel_str in lines:
            file_path = self._repo_dir / rel_str

            if not file_path.exists() or not file_path.is_file():
                logging.warning(f"File not found: {file_path}")
                continue

            if not is_text_file(file_path):
                logging.warning(
                    f"Potential non-text file detected at {file_path}"
                )
                continue

            if (ext := file_path.suffix) not in self._fences_map:
                continue

            block = self._format_file_block(
                rel_str, file_path, self._fences_map[ext]
            )

            if block is None:
                continue

            if current_md_path.exists():
                if current_md_path.stat().st_size >= self._max_bytes:
                    current_id += 1
                    current_md_path = output_name(current_id)

            with current_md_path.open("a", encoding="utf-8") as out:
                out.write(block)

        logging.info(
            f"Processed files into {current_id} markdown file(s) under "
            f"{self._output_dir}"
        )
