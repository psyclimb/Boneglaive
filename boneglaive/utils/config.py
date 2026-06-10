#!/usr/bin/env python3
"""
Configuration management for the game.
Handles loading/saving settings and provides defaults.
"""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

class DisplayMode(Enum):
    """Display mode options."""
    TEXT = "text"
    GRAPHICAL = "graphical"

class NetworkMode(Enum):
    """Network mode options."""
    SINGLE_PLAYER = "single"
    LOCAL_MULTIPLAYER = "local"
    VS_AI = "vs_ai"

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
    selected_map: str = "lime_foyer"
    
    # Network settings
    network_mode: str = NetworkMode.VS_AI.value
    player_name: str = "Player"

    # Profile settings
    current_profile: str = ""  # Name of currently selected profile

    # AI settings
    ai_difficulty: str = "medium"  # easy, medium, hard
    
    # Audio settings
    audio_enabled: bool = True
    music_volume: float = 0.7
    sfx_volume: float = 1.0

    # Interface settings
    ui_layout: str = "default"  # "default" or "reversed"

    # Controls
    custom_keybindings: Dict = None
    
    def __post_init__(self):
        if self.custom_keybindings is None:
            self.custom_keybindings = {}

class ConfigManager:
    """Manages loading, saving, and accessing game configuration."""

    def __init__(self, config_path: Optional[str] = None):
        from boneglaive.utils.paths import asset_path, user_config_dir

        # User config lives in a writable location (survives PyInstaller)
        self._user_config_path = Path(config_path) if config_path else user_config_dir() / "config.json"

        # Bundled default config (read-only inside _MEIPASS)
        self._default_config_path = Path(asset_path("config.json"))

        self.config = GameConfig()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration: user file first, fall back to bundled default."""
        for path in (self._user_config_path, self._default_config_path):
            try:
                if path.exists():
                    with open(path, 'r') as f:
                        config_dict = json.load(f)
                    for key, value in config_dict.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                    return
            except (json.JSONDecodeError, IOError):
                pass

    def save_config(self) -> None:
        """Save current configuration to the user config file."""
        try:
            self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
            config_dict = asdict(self.config)
            with open(self._user_config_path, 'w') as f:
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