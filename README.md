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

Samples are provided under [samples/](./samples/) directory. One can use the package directly from Python or use the CLI (recommended) as follows:

```bash
uv run remixfy --config '<path/to/repo.yaml>'
```

The following snipped documents the YAML file format:

```yaml
repomixfy:
  # URL point to the repository that will be cloned:
  url: https://github.com/OpenFOAM/OpenFOAM-13.git
  branch: master
  repo_dir: openfoam-13
  output_dir: openfoam-13_mix
  size_max: 4.0
  force_write: true

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

  ignore_dirs:
    - .git
    - wmake
    - Make
    - Doxygen

  ignore_ext:
    - .pdf
    - .png
    - .jpg
    - .jpeg
    - .gif
    - .svg
    - .gz
    - .tar

  fences_map:
    .C: c++
    .H: c++
    .cxx: c++
    .h: c++
```