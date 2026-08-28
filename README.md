# Re(po)Mixfy

Minimalistic repository-to-text package for feeding LLMs.

> This is a simple alternative to [repomix](https://github.com/yamadashy/repomix).

## 🔨 Install

The packaged is managed and installable using [uv](https://docs.astral.sh/uv/). You will also need [git](https://git-scm.com/) to be available in your machine.

The first option is to proceed as follows:

```bash
uv pip install git+https://github.com/wallytutor/remixfy.git
```

For contributing you need to clone and sync the project:

```bash
git clone https://github.com/wallytutor/remixfy.git
cd remixfy
uv sync

# Optionally, activate the environment for working here:
# Windows: .venv/Scripts/activate
# Linux: source .venv/bin/activate
```

## 🤷‍♂️ Usage

### `repomixfy`

Samples are provided under [samples/](./samples/) directory. One can use the package directly from Python or use the CLI (recommended) as follows:

```bash
uv run repomixfy --config '<path/to/repo.yaml>'
```

The following snipped documents the YAML file format:

```yaml
repomixfy:
  # Git repository URL to clone.
  url: https://github.com/OpenFOAM/OpenFOAM-13.git

  # Git branch to check out during clone.
  branch: master

  # Destination directory path for the cloned repository.
  repo_dir: openfoam-13

  # Destination directory path for the generated output files.
  output_dir: openfoam-13_mix

  # Maximum size of output files in MB.
  size_max: 4.0

  # Whether file extension matching should be case-sensitive.
  case_sensitive_ext: false

  # Whether to allow overwriting of outputs directory.
  force_write: true

  # List of file names to ignore.
  ignore_files:
    - .gitattributes
    - .gitignore
    - COPYING
    - Allwmake
    - Allwclean
    - Allmake
    - Allclean
    - Allrun
    - Alltest

  # List of directory names to ignore.
  ignore_dirs:
    - .git
    - wmake
    - Make
    - Doxygen

  # List of file extensions to ignore.
  ignore_ext:
    - .pdf
    - .png
    - .jpg
    - .jpeg
    - .gif
    - .svg
    - .gz
    - .tar

  # Map of fences to use for chunking. Key: file extension (with
  # leading dot), Value: fence name
  fences_map:
    .C: c++
    .H: c++
    .cxx: c++
    .h: c++
```

### `pagetree`

*WiP*

## 📃 To-Do

- [ ] Implement a sample case using the functional form of a fence map (text processing function) and document it. That might be the extraction of headers from OpenFOAM files.
