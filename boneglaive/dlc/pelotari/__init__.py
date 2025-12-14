#!/usr/bin/env python3
"""
PELOTARI DLC Plugin

The PELOTARI is a jai alai specialist with ricochet ball mechanics and frequency modulation.
This is a 5-glaive complexity unit focused on burst damage, buff control, and displacement.
"""

from pathlib import Path
import json

from .skills import PASSIVE_SKILL, ACTIVE_SKILLS

# Load unit configuration
config_path = Path(__file__).parent / "unit_config.json"
with open(config_path, 'r') as f:
    UNIT_CONFIG = json.load(f)

# Plugin metadata
PLUGIN_NAME = "pelotari"
PLUGIN_VERSION = "1.0.0"
REQUIRES_GAME_VERSION = "0.1.0"


def register_unit(game):
    """
    Called by game to register this DLC unit.

    Args:
        game: Game instance to register with

    Returns:
        dict: Unit registration data containing:
            - config: Unit configuration (stats, display info)
            - passive_skill: Passive skill class
            - active_skills: List of active skill classes
            - assets_path: Path to assets directory
    """
    return {
        'config': UNIT_CONFIG,
        'passive_skill': PASSIVE_SKILL,
        'active_skills': ACTIVE_SKILLS,
        'assets_path': Path(__file__).parent / 'assets',
        'plugin_name': PLUGIN_NAME,
        'plugin_version': PLUGIN_VERSION
    }


def initialize(game):
    """
    Optional initialization hook called when DLC is loaded.

    Args:
        game: Game instance
    """
    from boneglaive.utils.debug import logger
    logger.info(f"PELOTARI DLC v{PLUGIN_VERSION} loaded successfully")


__all__ = [
    'UNIT_CONFIG',
    'PASSIVE_SKILL',
    'ACTIVE_SKILLS',
    'register_unit',
    'initialize',
    'PLUGIN_NAME',
    'PLUGIN_VERSION',
    'REQUIRES_GAME_VERSION'
]
