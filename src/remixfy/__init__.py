# -*- coding: utf-8 -*-

import logging
import sys

from argparse import ArgumentParser
from pathlib import Path

from ruamel.yaml import YAML

from .repomixfy import RepoMixfy

logging.basicConfig(
    stream = sys.stdout,
    level  = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)

def main() -> None:
    print("Hello from remixfy!")
