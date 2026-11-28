"""Load project paths and application settings from config.yaml."""

from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    # Read YAML configuration and reject a document that is not a mapping.
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(f"{CONFIG_PATH} must contain a YAML object")

    return config