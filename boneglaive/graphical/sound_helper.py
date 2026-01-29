#!/usr/bin/env python3
"""
Sound Helper Functions
Utilities for playing sounds from animations.
"""


def play_sound(sound_key: str, category: str = "skills"):
    """
    Play a sound effect from within an animation.
    Safe wrapper that won't crash if sound system isn't initialized.

    Args:
        sound_key: Sound key (e.g., "judgement_throw", "pry_impact")
        category: Sound category (skills, impacts, ui, music)

    Returns:
        True if sound played successfully, False otherwise
    """
    try:
        from boneglaive.graphical.sound_manager import get_sound_manager
        sound_manager = get_sound_manager()
        return sound_manager.play(sound_key, category=category)
    except Exception as e:
        # Don't crash if sound fails - animations should continue
        return False
