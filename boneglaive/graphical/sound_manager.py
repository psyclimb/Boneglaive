#!/usr/bin/env python3
"""
Sound Manager for Boneglaive
Centralized system for loading, caching, and playing sound effects.
"""
import pygame
import os
from pathlib import Path
from typing import Dict, Optional
from boneglaive.utils.paths import asset_path


class SoundManager:
    """
    Centralized sound management system.

    Features:
    - Sound caching (load once, play many times)
    - Volume control per category (skills, impacts, UI, music)
    - Graceful fallback for missing sounds
    - Easy enable/disable for all sounds
    """

    def __init__(self, sounds_dir: Optional[str] = None, enabled: bool = True):
        """
        Initialize the sound manager.

        Args:
            sounds_dir: Path to sounds directory. If None, uses default location.
            enabled: Whether sounds are enabled globally
        """
        self.enabled = enabled

        # Determine sounds directory
        if sounds_dir is None:
            self.sounds_dir = Path(asset_path("sounds"))
        else:
            self.sounds_dir = Path(sounds_dir)

        # Sound cache: {sound_key: pygame.Sound}
        self._sound_cache: Dict[str, pygame.mixer.Sound] = {}

        # Volume levels per category (0.0 to 1.0)
        self.volumes = {
            "master": 1.0,
            "skills": 1.0,
            "impacts": 1.0,
            "ui": 1.0,
            "music": 1.0,
        }

        # Initialize pygame mixer
        self._init_mixer()

        # Track whether we've logged missing sounds to avoid spam
        self._missing_sounds = set()

    def _init_mixer(self):
        """Initialize pygame mixer if not already initialized."""
        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        except Exception as e:
            self.enabled = False

    def load_sound(self, sound_key: str, category: str = "skills") -> bool:
        """
        Load a sound file into cache.

        Args:
            sound_key: Sound identifier (e.g., "estrange", "judgement")
            category: Sound category (skills, impacts, ui, music)

        Returns:
            True if sound was loaded successfully, False otherwise
        """
        if not self.enabled:
            return False

        if sound_key in self._sound_cache:
            return True  # Already loaded

        # Construct file path: sounds/<category>/<sound_key>.wav
        sound_path = self.sounds_dir / category / f"{sound_key}.wav"

        if not sound_path.exists():
            # Try without category (flat directory structure)
            sound_path = self.sounds_dir / f"{sound_key}.wav"

        if not sound_path.exists():
            if sound_key not in self._missing_sounds:
                self._missing_sounds.add(sound_key)
            return False

        try:
            sound = pygame.mixer.Sound(str(sound_path))
            self._sound_cache[sound_key] = sound
            return True
        except Exception as e:
            return False

    def play(self, sound_key: str, category: str = "skills", loops: int = 0) -> bool:
        """
        Play a sound effect.

        Args:
            sound_key: Sound identifier (e.g., "estrange", "judgement")
            category: Sound category (skills, impacts, ui, music)
            loops: Number of times to loop (-1 for infinite)

        Returns:
            True if sound played successfully, False otherwise
        """
        if not self.enabled:
            return False

        # Load sound if not in cache
        if sound_key not in self._sound_cache:
            if not self.load_sound(sound_key, category):
                return False

        try:
            sound = self._sound_cache[sound_key]

            # Calculate final volume (master * category)
            volume = self.volumes["master"] * self.volumes.get(category, 1.0)
            sound.set_volume(volume)

            # Play sound
            sound.play(loops=loops)
            return True
        except Exception as e:
            return False

    def stop(self, sound_key: str):
        """Stop a currently playing sound."""
        if sound_key in self._sound_cache:
            try:
                self._sound_cache[sound_key].stop()
            except Exception as e:
                pass

    def stop_all(self):
        """Stop all currently playing sounds."""
        pygame.mixer.stop()

    def set_volume(self, category: str, volume: float):
        """
        Set volume for a category.

        Args:
            category: Category name (master, skills, impacts, ui, music)
            volume: Volume level (0.0 to 1.0)
        """
        if category in self.volumes:
            self.volumes[category] = max(0.0, min(1.0, volume))

    def enable(self):
        """Enable sound system."""
        self.enabled = True
        self._init_mixer()

    def disable(self):
        """Disable sound system."""
        self.enabled = False
        self.stop_all()

    def preload_sounds(self, sound_list: list, category: str = "skills"):
        """
        Preload a list of sounds for faster playback.

        Args:
            sound_list: List of sound keys to preload
            category: Sound category
        """
        for sound_key in sound_list:
            self.load_sound(sound_key, category)

    def clear_cache(self):
        """Clear the sound cache (useful for reloading sounds)."""
        self._sound_cache.clear()
        self._missing_sounds.clear()


# Global sound manager instance (singleton pattern)
_sound_manager_instance: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    """
    Get the global SoundManager instance (singleton).

    Returns:
        SoundManager instance
    """
    global _sound_manager_instance
    if _sound_manager_instance is None:
        _sound_manager_instance = SoundManager()
    return _sound_manager_instance


def init_sound_manager(sounds_dir: Optional[str] = None, enabled: bool = True) -> SoundManager:
    """
    Initialize the global SoundManager instance.

    Args:
        sounds_dir: Path to sounds directory
        enabled: Whether sounds are enabled globally

    Returns:
        SoundManager instance
    """
    global _sound_manager_instance
    _sound_manager_instance = SoundManager(sounds_dir=sounds_dir, enabled=enabled)
    return _sound_manager_instance
