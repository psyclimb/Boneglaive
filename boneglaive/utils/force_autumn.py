#!/usr/bin/env python3
"""
Force autumn season to be active for testing.
This overrides the seasonal detection to always return autumn.
"""

from boneglaive.utils.seasonal_events import SeasonalEvent

def get_active_season(test_date=None):
    """Override function that always returns autumn."""
    return SeasonalEvent.AUTUMN_EQUINOX

# Monkey patch the seasonal_events module
import boneglaive.utils.seasonal_events as seasonal_events
seasonal_events.get_active_season = get_active_season
seasonal_events.seasonal_manager.get_active_season = get_active_season

print("🍂 AUTUMN MODE ACTIVATED - Autumn Equinox forced active!")
print("   Stained Stones will now load as autumn variant")
print("   Look for 'Stained Stones ☀' in map selection")