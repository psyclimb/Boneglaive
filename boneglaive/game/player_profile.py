#!/usr/bin/env python3
"""
Player profile system for tracking stats and preferences.
Profiles are stored as JSON files in the profiles/ directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict
from boneglaive.utils.constants import UnitType
from boneglaive.utils.debug import logger


# Default profile directory (relative to project root)
PROFILES_DIR = Path(__file__).parent.parent.parent / "profiles"


@dataclass
class PlayerProfile:
    """
    Player profile with stats and preferences.
    Designed to be easily expandable with new fields.
    """
    name: str  # 8 character max

    # Game statistics
    wins: int = 0
    losses: int = 0
    games_played: int = 0

    # Unit selection statistics
    unit_picks: Dict[str, int] = field(default_factory=dict)

    # Expandable sections for future features
    achievements: Dict[str, bool] = field(default_factory=dict)
    preferences: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize unit picks for all unit types if not present."""
        if not self.unit_picks:
            self.unit_picks = {}

        # Ensure all unit types have entries
        for unit_type in UnitType:
            unit_name = unit_type.name
            if unit_name not in self.unit_picks:
                self.unit_picks[unit_name] = 0

    def record_win(self):
        """Record a win."""
        self.wins += 1
        self.games_played += 1
        logger.info(f"Profile {self.name}: Recorded win ({self.wins} total)")

    def record_loss(self):
        """Record a loss."""
        self.losses += 1
        self.games_played += 1
        logger.info(f"Profile {self.name}: Recorded loss ({self.losses} total)")

    def record_unit_pick(self, unit_type: UnitType):
        """Record a unit being picked."""
        unit_name = unit_type.name
        if unit_name not in self.unit_picks:
            self.unit_picks[unit_name] = 0
        self.unit_picks[unit_name] += 1
        logger.info(f"Profile {self.name}: Picked {unit_name} ({self.unit_picks[unit_name]} total)")

    def get_win_rate(self) -> float:
        """Calculate win rate as a percentage."""
        if self.games_played == 0:
            return 0.0
        return (self.wins / self.games_played) * 100

    def get_most_picked_unit(self) -> Optional[str]:
        """Get the name of the most picked unit."""
        if not self.unit_picks or all(count == 0 for count in self.unit_picks.values()):
            return None
        return max(self.unit_picks.items(), key=lambda x: x[1])[0]

    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerProfile':
        """Create profile from dictionary loaded from JSON."""
        return cls(**data)


class ProfileManager:
    """Manages player profiles - loading, saving, and switching."""

    def __init__(self, profiles_dir: Path = PROFILES_DIR):
        self.profiles_dir = profiles_dir
        self.current_profile: Optional[PlayerProfile] = None

        # Ensure profiles directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Profile directory: {self.profiles_dir}")

    def _get_profile_path(self, name: str) -> Path:
        """Get the file path for a profile."""
        # Sanitize name for filename (remove special chars)
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-'))
        return self.profiles_dir / f"{safe_name}.json"

    def create_profile(self, name: str) -> PlayerProfile:
        """
        Create a new profile.

        Args:
            name: Player name (will be truncated to 8 characters)

        Returns:
            The newly created profile

        Raises:
            ValueError: If profile already exists
        """
        # Enforce 8 character limit
        name = name[:8].strip().upper()

        if not name:
            raise ValueError("Profile name cannot be empty")

        profile_path = self._get_profile_path(name)
        if profile_path.exists():
            raise ValueError(f"Profile '{name}' already exists")

        # Create new profile
        profile = PlayerProfile(name=name)
        self.save_profile(profile)

        logger.info(f"Created new profile: {name}")
        return profile

    def load_profile(self, name: str) -> Optional[PlayerProfile]:
        """
        Load a profile from disk.

        Args:
            name: Profile name to load

        Returns:
            The loaded profile, or None if not found
        """
        profile_path = self._get_profile_path(name)
        if not profile_path.exists():
            logger.warning(f"Profile not found: {name}")
            return None

        try:
            with open(profile_path, 'r') as f:
                data = json.load(f)

            profile = PlayerProfile.from_dict(data)
            logger.info(f"Loaded profile: {name}")
            return profile
        except Exception as e:
            logger.error(f"Error loading profile {name}: {e}")
            return None

    def save_profile(self, profile: PlayerProfile):
        """Save a profile to disk."""
        profile_path = self._get_profile_path(profile.name)

        try:
            with open(profile_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            logger.info(f"Saved profile: {profile.name}")
        except Exception as e:
            logger.error(f"Error saving profile {profile.name}: {e}")

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profiles.append(data['name'])
            except Exception as e:
                logger.error(f"Error reading profile {profile_file}: {e}")

        return sorted(profiles)

    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.

        Args:
            name: Profile name to delete

        Returns:
            True if deleted, False if not found
        """
        profile_path = self._get_profile_path(name)
        if not profile_path.exists():
            return False

        try:
            profile_path.unlink()
            logger.info(f"Deleted profile: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting profile {name}: {e}")
            return False

    def set_current_profile(self, profile: PlayerProfile):
        """Set the currently active profile."""
        self.current_profile = profile
        logger.info(f"Active profile: {profile.name}")

    def get_current_profile(self) -> Optional[PlayerProfile]:
        """Get the currently active profile."""
        return self.current_profile


# Global profile manager instance
profile_manager = ProfileManager()
