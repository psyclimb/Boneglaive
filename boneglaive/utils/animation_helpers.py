#!/usr/bin/env python3
"""
Helper functions for animations that respect the global animation speed setting.
"""

import time
from boneglaive.utils.config import ConfigManager

def sleep_with_animation_speed(duration):
    """
    Sleep for the specified duration, adjusted by the global animation speed.
    
    Args:
        duration (float): The base sleep duration in seconds
        
    Returns:
        None
    """
    config = ConfigManager()
    animation_speed = config.get('animation_speed', 1.0)
    
    # Apply animation speed - higher speed means shorter duration
    if animation_speed > 0:
        adjusted_duration = duration / animation_speed
        # Set a minimum sleep time to prevent zero-duration animations
        adjusted_duration = max(0.01, adjusted_duration)
        time.sleep(adjusted_duration)
    else:
        # Default fallback if animation_speed is 0 or negative
        time.sleep(duration)