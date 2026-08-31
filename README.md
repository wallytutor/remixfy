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

Samples are provided under [samples/repomixfy](./samples/repomixfy) directory. One can use the package directly from Python or use the CLI (recommended) as follows:

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

Samples are provided under [samples/pagetree](./samples/pagetree) directory. One can use the package directly from Python or use the CLI (recommended) as follows:

```bash
uv run pagetree --config '<path/to/repo.yaml>'
```

The following snipped documents the YAML file format:

```yaml
pagetree:
  # The base URL where we start the scraping:
  url: https://doc.cfd.direct/openfoam/user-guide-v13/contents

  # The domain under which links should be confined: only absolute
  # links living under this domain/URL are going to be fetched. If
  # relative_links == true, then only those found to live under this
  # parent URL are retrieved.
  parent: https://doc.cfd.direct/openfoam/user-guide-v13/

  # If true, scrape relative links too, following the rules of parent.
  relative_links: true

  # Directory under which the scraped content is going to be written.
  output_dir: openfoam-guide-v13_mix

  # If true, overwrite existing files.
  force_write: true

  # Limits for the scraping process:
  max_depth: 5
  max_pages: 1000
  request_delay: 1

  # Instead of writing the whole page contents, extract only what
  # is found under this tag. If id or class is supplied (non-null),
  # these are used to further filter the parent tag.
  parent_tag:
    tag_name: body
    id: null
    class: null

  # Skip any tag whose tag name is in this list:
  skip_tags:
    - header
    - footer
    - script

  # Skip classes:
  skip_classes:
    - crosslinks
    - widget_call_to_action

  # Skip id's:
  skip_ids:
    - content-top

  # If true, convert pages to Markdown format using Pandoc.
  convert_md: true

  # If true, then pages are stripped of all HTML tags (id, class, etc)
  # so that a minimalistic document is produced. It is ignored if
  # convert_md is set to true (single output format).
  plain_html: false

  # If true, concatenate all pages into a single file in the order of
  # retrieval. The file is named _pagetree.<ext> (where <ext> is the
  # output format: md or html depending on convert_md). A comment with
  # the format <!-- {source-url} --> is added before the contents to
  # keep files identifiable in the final file.
  concatenate: true
```

## 📃 To-Do

- [ ] Implement a sample case using the functional form of a fence map (text processing function) and document it. That might be the extraction of headers from OpenFOAM files.
