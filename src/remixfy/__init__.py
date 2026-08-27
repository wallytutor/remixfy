# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import fnmatch
import logging
import os
import sys

from pathlib import Path
from subprocess import run

from .tools import (
    is_text_file,
    repository_name,
)

logging.basicConfig(
    stream = sys.stdout,
    level  = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)


class RepoMixfy:
    __slots__ = (
        "_url",
        "_branch",
        "_repo_dir",
        "_output_dir",
        "_ignore_files",
        "_ignore_dirs",
        "_ignore_ext",
        "_size_max",
        "_fences_map",
    )

    def __init__(
            self,
            url: str,
            branch: str = "main",
            repo_dir: str | Path | None = None,
            output_dir: str | Path | None = None,
            ignore_files: list[str] | None = None,
            ignore_dirs: list[str] | None = None,
            ignore_ext: list[str] | None = None,
            size_max: float = 2.0,
            fences_map: dict | None = None
        ) -> None:
        self._url: str = url
        self._branch: str = branch
        self._repo_dir: Path = self._resolve_repo_dir(repo_dir)
        self._output_dir: Path = self._resolve_output_dir(output_dir)
        self._ignore_files: list[str] = ignore_files or []
        self._ignore_dirs: list[str] = ignore_dirs or []
        self._ignore_ext: list[str] = ignore_ext or []
        self._size_max: float = size_max
        self._fences_map: dict = fences_map or {}

        self._init_clone()
        self._init_files()
        self._process_files()

    def _resolve_repo_dir(self, repo_dir) -> Path:
        if not repo_dir:
            repo_dir = repository_name(self._url)

        repo_dir = self._resolve_dir(repo_dir)
        logging.info(f"Repository at {repo_dir}")
        return repo_dir

    def _resolve_output_dir(self, output_dir) -> Path:
        if not output_dir:
            output_dir = self._repo_dir.name + "_mix"

        output_dir = self._resolve_dir(output_dir)
        logging.info(f"Output at {output_dir}")
        return output_dir

    def _resolve_dir(self, tmp_dir) -> Path:
        if isinstance(tmp_dir, str):
            tmp_dir = Path(tmp_dir)

        if not tmp_dir.is_absolute():
            tmp_dir = Path.cwd().joinpath(tmp_dir)


        return tmp_dir

    def _is_dir_ignored(self, dir_parts: tuple[str, ...]) -> bool:
        """ Check if directory parts match any rule in _ignore_dirs. """
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

    def _init_clone(self) -> None:
        """ Initialize clone of the repository. """
        if self._repo_dir.exists() and self._repo_dir.is_dir():
            logging.info(f"Repository already cloned at {self._repo_dir}")
            return

        run(
            [
                "git",
                "clone",
                "--branch",
                self._branch,
                self._url,
                self._repo_dir
            ],
            check=True,
            capture_output=True
        )

    def _init_files(self) -> None:
        """ Initialize .repomixfy file with repository files list. """
        if not self._repo_dir.exists():
            return

        self._output_dir.mkdir(parents=True, exist_ok=True)

        repomixfy_path = self._output_dir / ".repomixfy"

        ignore_ext = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self._ignore_ext
        }

        file_paths: list[str] = []

        for root, dirs, files in os.walk(self._repo_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self._repo_dir)

            dirs[:] = [
                d for d in dirs
                if not self._is_dir_ignored((rel_root / d).parts)
            ]

            for file in files:
                # if file == ".repomixfy":
                #     continue

                file_path = root_path / file
                rel_path = file_path.relative_to(self._repo_dir)

                if self._is_dir_ignored(rel_path.parts[:-1]):
                    continue

                if any(
                    file == pat or fnmatch.fnmatch(file, pat)
                    for pat in self._ignore_files
                ):
                    continue

                if file_path.suffix.lower() in ignore_ext:
                    continue

                file_paths.append(rel_path.as_posix())

        file_paths.sort()

        with repomixfy_path.open("w", encoding="utf-8") as f:
            for rel_path in file_paths:
                f.write(f"{rel_path}\n")

        logging.info(
            f"Created .repomixfy with {len(file_paths)} files at "
            f"{repomixfy_path}"
        )

    def _process_files(self) -> None:
        """ Process files listed in .repomixfy into markdown chunks. """
        repomixfy_path = self._output_dir / ".repomixfy"

        if not repomixfy_path.exists():
            logging.warning(f".repomixfy file missing at {repomixfy_path}")
            return

        reponame = self._repo_dir.name
        max_bytes = int(self._size_max * 1024 * 1024)
        current_id = 1
        current_md_path = self._output_dir / f"{reponame}-{current_id}.md"

        for old_md in self._output_dir.glob(f"{reponame}-*.md"):
            try:
                old_md.unlink()
            except OSError:
                pass

        with repomixfy_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            rel_str = line.strip()

            if not rel_str:
                continue

            file_path = self._repo_dir / rel_str

            if not file_path.exists() or not file_path.is_file():
                logging.warning(f"File not found: {file_path}")
                continue

            if not is_text_file(file_path):
                logging.warning(
                    f"Potential non-text file detected at {file_path}"
                )
                continue

            ext = file_path.suffix

            if ext not in self._fences_map:
                continue

            fence_val = self._fences_map[ext]

            try:
                content = file_path.read_text(
                    encoding="utf-8", errors="replace"
                )
            except Exception as err:
                logging.warning(f"Failed to read {file_path}: {err}")
                continue

            if callable(fence_val):
                try:
                    processed = fence_val(content)
                except TypeError:
                    processed = fence_val(content, file_path)

                if isinstance(processed, str):
                    if (
                        processed.startswith("`")
                        or processed.startswith("#")
                        or processed.startswith("File:")
                    ):
                        block = f"{processed}\n\n"
                    else:
                        block = f"File: {rel_str}\n```\n{processed}\n```\n\n"
                else:
                    continue

            else:
                lang = str(fence_val)
                block = f"File: {rel_str}\n```{lang}\n{content}\n```\n\n"

            if current_md_path.exists():
                if current_md_path.stat().st_size >= max_bytes:
                    current_id += 1
                    current_md_path = (
                        self._output_dir / f"{reponame}-{current_id}.md"
                    )

            with current_md_path.open("a", encoding="utf-8") as out:
                out.write(block)

        logging.info(
            f"Processed files into {current_id} markdown file(s) under "
            f"{self._output_dir}"
        )





def main() -> None:
    print("Hello from remixfy!")
