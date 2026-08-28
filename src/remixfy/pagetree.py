# -*- coding: utf-8 -*-

import fnmatch
import logging
import math
import os
import shutil
import sys

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .tools import (
    resolve_repo_dir,
    resolve_output_dir,
)

logging.basicConfig(
    stream = sys.stdout,
    level  = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("placeholder for pagetree")
