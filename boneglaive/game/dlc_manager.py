#!/usr/bin/env python3
"""
DLC Plugin Manager for Boneglaive.

Handles discovery, loading, and registration of DLC units.
"""

import importlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType, UNIT_STATS, UNIT_SYMBOLS, UNIT_DISPLAY_NAMES, ATTACK_EFFECTS, GP_ELIGIBLE_UNITS


class DLCManager:
    """Manages DLC unit plugins."""

    def __init__(self, dlc_directory: Optional[Path] = None):
        """
        Initialize DLC manager.

        Args:
            dlc_directory: Path to DLC folder (default: boneglaive/dlc/)
        """
        if dlc_directory is None:
            # Default to boneglaive/dlc/ directory
            dlc_directory = Path(__file__).parent.parent / "dlc"

        self.dlc_directory = dlc_directory
        self.loaded_units: Dict[str, Dict[str, Any]] = {}
        self.unit_type_mappings: Dict[str, int] = {}  # unit_id -> enum value
        self.next_enum_value = 100  # Start DLC units at 100 to avoid conflicts

        logger.info(f"DLC Manager initialized: {self.dlc_directory}")

    def discover_dlc(self) -> List[str]:
        """
        Discover all DLC units in the DLC directory.

        Returns:
            List of discovered DLC unit IDs
        """
        if not self.dlc_directory.exists():
            logger.warning(f"DLC directory not found: {self.dlc_directory}")
            return []

        discovered = []

        # Scan for DLC folders
        for item in self.dlc_directory.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith('_') or item.name.startswith('.'):
                continue  # Skip special folders

            # Check for required files
            init_file = item / "__init__.py"
            config_file = item / "unit_config.json"

            if init_file.exists() and config_file.exists():
                discovered.append(item.name)
                logger.info(f"Discovered DLC unit: {item.name}")
            else:
                logger.warning(f"Incomplete DLC in {item.name}: missing __init__.py or unit_config.json")

        return discovered

    def load_dlc_unit(self, unit_id: str) -> bool:
        """
        Load a specific DLC unit.

        Args:
            unit_id: DLC unit identifier (folder name)

        Returns:
            bool: True if loaded successfully
        """
        unit_path = self.dlc_directory / unit_id

        if not unit_path.exists():
            logger.error(f"DLC unit not found: {unit_id}")
            return False

        try:
            # Import the DLC module
            module_name = f"boneglaive.dlc.{unit_id}"
            if module_name in sys.modules:
                # Reload if already imported
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # Get registration data
            if not hasattr(module, 'register_unit'):
                logger.error(f"DLC unit {unit_id} missing register_unit() function")
                return False

            registration_data = module.register_unit(None)  # Pass None for now, game instance later

            # Validate registration data
            if not self._validate_registration(registration_data, unit_id):
                return False

            # Create dynamic UnitType enum value
            enum_value = self.next_enum_value
            self.next_enum_value += 1

            # Store unit data
            self.loaded_units[unit_id] = {
                'registration': registration_data,
                'module': module,
                'enum_value': enum_value
            }

            self.unit_type_mappings[unit_id] = enum_value

            # Register with game constants
            self._register_unit_constants(unit_id, registration_data, enum_value)

            # Register skills with skills registry
            self._register_unit_skills(unit_id, registration_data, enum_value)

            logger.info(f"Successfully loaded DLC unit: {unit_id} (enum={enum_value})")

            # Call initialization hook if exists
            if hasattr(module, 'initialize'):
                module.initialize(None)  # Pass game instance when available

            return True

        except Exception as e:
            logger.error(f"Failed to load DLC unit {unit_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_all_dlc(self) -> int:
        """
        Discover and load all DLC units.

        Returns:
            int: Number of units loaded successfully
        """
        discovered = self.discover_dlc()
        loaded_count = 0

        for unit_id in discovered:
            if self.load_dlc_unit(unit_id):
                loaded_count += 1

        logger.info(f"Loaded {loaded_count}/{len(discovered)} DLC units")
        return loaded_count

    def _validate_registration(self, data: Dict[str, Any], unit_id: str) -> bool:
        """
        Validate DLC registration data.

        Args:
            data: Registration data dict
            unit_id: Unit identifier

        Returns:
            bool: True if valid
        """
        required_keys = ['config', 'passive_skill', 'active_skills', 'assets_path']

        for key in required_keys:
            if key not in data:
                logger.error(f"DLC unit {unit_id} missing required key: {key}")
                return False

        # Validate config
        config = data['config']
        required_config_keys = ['unit_name', 'unit_id', 'stats', 'ascii']

        for key in required_config_keys:
            if key not in config:
                logger.error(f"DLC unit {unit_id} config missing key: {key}")
                return False

        # Validate stats
        stats = config['stats']
        required_stats = ['hp', 'attack', 'defense', 'move_range', 'attack_range']

        for stat in required_stats:
            if stat not in stats:
                logger.error(f"DLC unit {unit_id} missing stat: {stat}")
                return False

        return True

    def _register_unit_constants(self, unit_id: str, registration_data: Dict[str, Any],
                                 enum_value: int) -> None:
        """
        Register DLC unit with game constants.

        Args:
            unit_id: Unit identifier
            registration_data: Registration data
            enum_value: Enum value for this unit
        """
        config = registration_data['config']
        stats = config['stats']
        ascii_config = config['ascii']

        # Create dynamic enum member
        # Note: This is a workaround since we can't modify Enum at runtime properly
        # We'll store it in a separate dict for DLC units
        setattr(UnitType, unit_id.upper(), enum_value)

        # Register stats
        UNIT_STATS[enum_value] = (
            stats['hp'],
            stats['attack'],
            stats['defense'],
            stats['move_range'],
            stats['attack_range']
        )

        # Register symbol
        UNIT_SYMBOLS[enum_value] = ascii_config['symbol']

        # Register display name
        UNIT_DISPLAY_NAMES[enum_value] = config.get('display_name', config['unit_name'])

        # Register attack effect
        if 'attack_effect' in ascii_config:
            ATTACK_EFFECTS[enum_value] = ascii_config['attack_effect']

        # Register GP eligibility
        if config.get('gp_eligible', True):
            GP_ELIGIBLE_UNITS.add(enum_value)

        logger.debug(f"Registered constants for {unit_id}: enum={enum_value}, stats={UNIT_STATS[enum_value]}")

    def _register_unit_skills(self, unit_id: str, registration_data: Dict[str, Any],
                              enum_value: int) -> None:
        """
        Register DLC unit skills with the skills registry.

        Args:
            unit_id: Unit identifier
            registration_data: Registration data
            enum_value: Enum value for this unit
        """
        from boneglaive.game.skills.registry import UNIT_SKILLS

        # Get skills from registration data
        passive_skill_class = registration_data.get('passive_skill')
        active_skill_classes = registration_data.get('active_skills', [])

        # Register skills using uppercase unit_id as key (matches base unit format)
        # DLC skills are classes, so instantiate them to match the registry format
        skill_entry = {}
        if passive_skill_class:
            skill_entry['passive'] = passive_skill_class()  # Create instance
        if active_skill_classes:
            skill_entry['active'] = [skill_class() for skill_class in active_skill_classes]  # Create instances

        # Register with uppercase name
        UNIT_SKILLS[unit_id.upper()] = skill_entry

        logger.debug(f"Registered skills for {unit_id}: passive={passive_skill_class is not None}, active={len(active_skill_classes)}")

    def get_unit_data(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """
        Get loaded unit data.

        Args:
            unit_id: Unit identifier

        Returns:
            Dict with unit data, or None if not loaded
        """
        return self.loaded_units.get(unit_id)

    def get_loaded_units(self) -> List[str]:
        """
        Get list of all loaded DLC unit IDs.

        Returns:
            List of unit IDs
        """
        return list(self.loaded_units.keys())

    def is_dlc_unit(self, unit_type_or_id) -> bool:
        """
        Check if a unit is a DLC unit.

        Args:
            unit_type_or_id: UnitType enum value or unit_id string

        Returns:
            bool: True if DLC unit
        """
        if isinstance(unit_type_or_id, str):
            return unit_type_or_id in self.loaded_units

        # Check enum value
        if isinstance(unit_type_or_id, int):
            return unit_type_or_id >= 100  # DLC units start at 100

        # Check UnitType enum
        if hasattr(unit_type_or_id, 'value'):
            return unit_type_or_id.value >= 100

        return False


# Global DLC manager instance
_dlc_manager: Optional[DLCManager] = None


def get_dlc_manager() -> DLCManager:
    """
    Get global DLC manager instance.

    Returns:
        DLCManager instance
    """
    global _dlc_manager
    if _dlc_manager is None:
        _dlc_manager = DLCManager()
    return _dlc_manager


def initialize_dlc_system() -> int:
    """
    Initialize DLC system and load all DLC units.

    Returns:
        int: Number of units loaded
    """
    manager = get_dlc_manager()
    return manager.load_all_dlc()
