# -*- coding: utf-8 -*-

from pathlib import Path
from remixfy import RepoMixfy

HERE = Path(__file__).parent


RepoMixfy(
    url = "https://github.com/OpenFOAM/OpenFOAM-13.git",
    branch = "master",
    repo_dir = HERE / "openfoam-13",
    output_dir = HERE / "openfoam-13_mix",
    ignore_files = [
        ".gitattributes",
        ".gitignore",
        "COPYING",
        "Allwmake",
        "Allwclean",
        "Allmake",
        "Allclean",
        "Allrun",
        "Alltest",
    ],
    ignore_dirs = [
        ".git",
        "wmake",
        "Make",
        "Doxygen",
    ],
    ignore_ext = [
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".gz",
        ".tar",
    ],
    fences_map = {
        ".C": "c++",
        ".H": "c++",
        ".cxx": "c++",
        ".h": "c++",
    }
)
