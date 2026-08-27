# -*- coding: utf-8 -*-

import logging
import sys

from argparse import ArgumentParser, Namespace
from pathlib import Path

from ruamel.yaml import YAML

from .repomixfy import RepoMixfy

logging.basicConfig(
    stream = sys.stdout,
    level  = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)


def main(cli_args: list[str] | None = None) -> None:
    """ Main entry point for the remixfy CLI. """
    args = parse_arguments(cli_args)
    config_path = Path(args.config).resolve()
    kwargs = load_yaml(config_path)
    RepoMixfy(**kwargs, base_dir=config_path.parent)


def parse_arguments(cli_args: list[str] | None = None) -> Namespace:
    """ Parse the arguments from the command line. """
    parser = ArgumentParser(
        description = "Remixfy repository content extractor."
    )
    parser.add_argument(
        "-c", "--config",
        required=True,
        type=str,
        help="Path to YAML configuration file"
    )
    return parser.parse_args(cli_args)


def load_yaml(config_path: Path) -> dict:
    """ Load the YAML configuration file as keywords. """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    yaml = YAML(typ="safe")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid YAML configuration format in {config_path}"
        )

    kwargs = data.get("repomixfy", data)

    if not isinstance(kwargs, dict):
        raise ValueError(
            f"Invalid 'repomixfy' configuration block in {config_path}"
        )

    return kwargs
