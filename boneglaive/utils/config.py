#!/usr/bin/env python3
"""
Configuration management for the game.
Handles loading/saving settings and provides defaults.
"""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, Optional

class DisplayMode(Enum):
    """Display mode options."""
    TEXT = "text"
    GRAPHICAL = "graphical"

@dataclass
class GameConfig:
    """Game configuration settings."""
    # Display settings
    display_mode: str = DisplayMode.TEXT.value
    window_width: int = 800
    window_height: int = 600
    fullscreen: bool = False
    
    # Gameplay settings
    animation_speed: float = 1.0
    show_grid: bool = True
    
    # Audio settings
    audio_enabled: bool = True
    music_volume: float = 0.7
    sfx_volume: float = 1.0
    
    # Controls
    custom_keybindings: Dict = None
    
    def __post_init__(self):
        if self.custom_keybindings is None:
            self.custom_keybindings = {}

class ConfigManager:
    """Manages loading, saving, and accessing game configuration."""
    
    DEFAULT_CONFIG_PATH = "config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = GameConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or use defaults."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_dict = json.load(f)
                    
                    # Update config with loaded values
                    for key, value in config_dict.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}. Using defaults.")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            config_dict = asdict(self.config)
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get a configuration value."""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value) -> None:
        """Set a configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            
    def is_text_mode(self) -> bool:
        """Check if display mode is text-based."""
        return self.config.display_mode == DisplayMode.TEXT.value