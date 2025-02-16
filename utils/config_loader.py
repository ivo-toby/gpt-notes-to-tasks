"""
Configuration loader module.

Provides functionality to load YAML configuration files with error handling.
"""

import yaml
from yaml.parser import ParserError


def load_config(config_file):
    """
    Load and parse a YAML configuration file.

    Args:
        config_file (str): Path to the YAML configuration file

    Returns:
        dict: Parsed configuration dictionary

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ParserError: If the YAML file is invalid
        ValueError: If the configuration is empty
    """
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if config is None:
                raise ValueError(f"Empty configuration file: {config_file}")
            return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except ParserError as e:
        raise ParserError(f"Invalid YAML in configuration file {config_file}: {str(e)}")
