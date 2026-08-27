# -*- coding: utf-8 -*-

from pathlib import Path
from remixfy import RepoMixfy, repository_name, main


def test_repository_name():
    url = "https://github.com/OpenFOAM/OpenFOAM-13.git"
    assert repository_name(url) == "OpenFOAM-13"


def test_init_files():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "test_repo"
        repo_dir.mkdir()

        (repo_dir / "file1.txt").write_text("hello", encoding="utf-8")
        (repo_dir / "Allwmake").write_text("clean", encoding="utf-8")
        (repo_dir / "image.png").write_text("img", encoding="utf-8")

        git_dir = repo_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config", encoding="utf-8")

        sub_dir = repo_dir / "src"
        sub_dir.mkdir()
        (sub_dir / "main.py").write_text("print('hi')", encoding="utf-8")

        # Test deep nested directory matching
        make_dir = sub_dir / "OpenFOAM" / "Make"
        make_dir.mkdir(parents=True)
        (make_dir / "options").write_text("options", encoding="utf-8")

        # Test multi-level directory path matching
        rules_dir = repo_dir / "wmake" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "linux").write_text("rule", encoding="utf-8")

        # Test glob pattern directory matching
        build_dir = repo_dir / "build_temp"
        build_dir.mkdir()
        (build_dir / "temp.o").write_text("obj", encoding="utf-8")

        # Test anchored vs unanchored path matching
        root_bin = repo_dir / "bin" / "tools"
        root_bin.mkdir(parents=True)
        (root_bin / "root_tool.sh").write_text("sh", encoding="utf-8")

        nested_bin = sub_dir / "bin" / "tools"
        nested_bin.mkdir(parents=True)
        (nested_bin / "nested_tool.sh").write_text("sh", encoding="utf-8")

        ignore_files = ["Allwmake"]
        ignore_dirs = [".git", "Make", "wmake/rules", "build_*", "./bin/tools"]
        ignore_ext = [".png"]

        mix = RepoMixfy.__new__(RepoMixfy)
        mix._repo_dir = repo_dir
        mix._output_dir = repo_dir
        mix._ignore_files = ignore_files
        mix._ignore_dirs = ignore_dirs
        mix._ignore_ext = ignore_ext
        mix._repomixfy_path = repo_dir / ".repomixfy"

        mix._max_bytes = int(2.0 * 1024 ** 2)
        mix._fences_map = {
            ".txt": "text",
            ".py": "python",
            ".sh": lambda content: f"SHELL:\n{content}"
        }

        mix._init_files(False)

        repomixfy_file = repo_dir / ".repomixfy"
        assert repomixfy_file.exists()

        lines = repomixfy_file.read_text(encoding="utf-8").splitlines()
        # "./bin/tools" ignored root bin/tools, but src/bin/tools is kept
        assert lines == ["file1.txt", "src/bin/tools/nested_tool.sh", "src/main.py"]

        mix._process_files()

        md_file = repo_dir / "test_repo-1.md"
        assert md_file.exists()
        md_text = md_file.read_text(encoding="utf-8")
        assert "File: file1.txt" in md_text
        assert "```text\nhello\n```" in md_text
        assert "SHELL:\nsh" in md_text


def test_main():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        repo_dir = tmp_path / "my_repo"
        repo_dir.mkdir()
        (repo_dir / "app.py").write_text("print('hello')", encoding="utf-8")

        config_file = tmp_path / "config.yaml"
        yaml_content = f"""
repomixfy:
  url: "https://github.com/user/my_repo.git"
  repo_dir: "my_repo"
  output_dir: "my_output"
  fences_map:
    .py: python
"""
        config_file.write_text(yaml_content, encoding="utf-8")

        main(["--config", str(config_file)])

        out_dir = tmp_path / "my_output"
        assert out_dir.exists()
        repomixfy_file = out_dir / ".repomixfy"
        assert repomixfy_file.exists()
        md_file = out_dir / "my_repo-1.md"
        assert md_file.exists()
        assert "app.py" in md_file.read_text(encoding="utf-8")


def test_main_default_dirs():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        repo_dir = tmp_path / "sample_repo"
        repo_dir.mkdir()
        (repo_dir / "code.py").write_text("x = 1", encoding="utf-8")

        config_file = tmp_path / "config.yaml"
        yaml_content = f"""
repomixfy:
  url: "https://github.com/user/sample_repo.git"
  fences_map:
    .py: python
"""
        config_file.write_text(yaml_content, encoding="utf-8")

        main(["-c", str(config_file)])

        out_dir = tmp_path / "sample_repo_mix"
        assert out_dir.exists()
        assert (out_dir / ".repomixfy").exists()


def tests():
    test_repository_name()
    test_init_files()
    test_main()
    test_main_default_dirs()


if __name__ == "__main__":
    tests()

