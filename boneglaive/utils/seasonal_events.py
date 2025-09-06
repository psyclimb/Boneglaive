#!/usr/bin/env python3
"""
Seasonal event scheduling system for Boneglaive based on solstices and equinoxes.
Automatically detects and activates seasonal content based on astronomical events.
"""

import datetime
from enum import Enum
from typing import Optional, List, Tuple, Dict
import os

from boneglaive.utils.debug import logger


class SeasonalEvent(Enum):
    """Available seasonal events based on astronomical cycles."""
    SPRING_EQUINOX = "spring_equinox"     # March 20-21
    SUMMER_SOLSTICE = "summer_solstice"   # June 20-21
    AUTUMN_EQUINOX = "autumn_equinox"     # September 22-23
    WINTER_SOLSTICE = "winter_solstice"   # December 21-22


class SeasonalEventManager:
    """Manages seasonal event scheduling and content activation based on astronomical events."""
    
    def __init__(self):
        """Initialize the seasonal event manager with astronomical date configurations."""
        # Seasonal event date ranges (month, day) tuples
        # Includes buffer days around actual astronomical events
        self.seasonal_dates = {
            SeasonalEvent.SPRING_EQUINOX: [
                (3, 19), (3, 20), (3, 21), (3, 22)  # Spring Equinox period
            ],
            SeasonalEvent.SUMMER_SOLSTICE: [
                (6, 19), (6, 20), (6, 21), (6, 22)  # Summer Solstice period
            ],
            SeasonalEvent.AUTUMN_EQUINOX: [
                (9, 21), (9, 22), (9, 23), (9, 24)  # Autumn Equinox period
            ],
            SeasonalEvent.WINTER_SOLSTICE: [
                (12, 20), (12, 21), (12, 22), (12, 23)  # Winter Solstice period
            ],
        }
        
        # Seasonal display names for UI/logging
        self.seasonal_names = {
            SeasonalEvent.SPRING_EQUINOX: "Spring Equinox",
            SeasonalEvent.SUMMER_SOLSTICE: "Summer Solstice", 
            SeasonalEvent.AUTUMN_EQUINOX: "Autumn Equinox",
            SeasonalEvent.WINTER_SOLSTICE: "Winter Solstice",
        }
        
        # Seasonal themes and descriptions
        self.seasonal_themes = {
            SeasonalEvent.SPRING_EQUINOX: {
                "theme": "Renewal and Growth",
                "description": "Light and darkness in perfect balance as life awakens",
                "colors": ["green", "light_yellow", "soft_blue"]
            },
            SeasonalEvent.SUMMER_SOLSTICE: {
                "theme": "Peak Light and Power",
                "description": "The longest day brings maximum energy and intensity",
                "colors": ["bright_yellow", "orange", "gold"]
            },
            SeasonalEvent.AUTUMN_EQUINOX: {
                "theme": "Harvest and Balance",
                "description": "Equal day and night as the world prepares for rest",
                "colors": ["orange", "red", "brown", "dark_yellow"]
            },
            SeasonalEvent.WINTER_SOLSTICE: {
                "theme": "Deepest Night and Reflection", 
                "description": "The longest night brings contemplation and inner strength",
                "colors": ["blue", "dark_blue", "purple", "silver"]
            },
        }
    
    def get_active_season(self, test_date: Optional[datetime.date] = None) -> Optional[SeasonalEvent]:
        """
        Check if today (or test_date) matches any seasonal event dates.
        
        Args:
            test_date: Optional date for testing purposes. Uses today() if None.
            
        Returns:
            Active SeasonalEvent or None if no seasonal event is active.
        """
        check_date = test_date or datetime.date.today()
        current_date = (check_date.month, check_date.day)
        
        for season, dates in self.seasonal_dates.items():
            if current_date in dates:
                theme = self.seasonal_themes[season]
                logger.info(f"Seasonal event active: {self.seasonal_names[season]} - {theme['theme']}")
                return season
        
        return None
    
    def get_seasonal_display_name(self, season: SeasonalEvent) -> str:
        """Get the display name for a seasonal event."""
        return self.seasonal_names.get(season, season.value.replace('_', ' ').title())
    
    def get_seasonal_theme(self, season: SeasonalEvent) -> Dict:
        """Get the theme information for a seasonal event."""
        return self.seasonal_themes.get(season, {})
    
    def is_seasonal_content_available(self, season: SeasonalEvent, content_type: str = "map") -> bool:
        """
        Check if seasonal content exists for the given season.
        
        Args:
            season: The seasonal event to check
            content_type: Type of content ("map", "unit", "theme", etc.)
            
        Returns:
            True if seasonal content directory/files exist
        """
        if content_type == "map":
            # Check if seasonal maps directory exists
            seasonal_maps_dir = os.path.join("maps", "seasonal", season.value)
            return os.path.exists(seasonal_maps_dir) and os.path.isdir(seasonal_maps_dir)
        
        # Future: Add checks for other content types (units, themes, etc.)
        return False
    
    def get_seasonal_map_path(self, base_map_name: str, season: SeasonalEvent) -> Optional[str]:
        """
        Get the path to a seasonal variant of a map.
        
        Args:
            base_map_name: The base map name (e.g., "lime_foyer")
            season: The seasonal event
            
        Returns:
            Path to seasonal map file if it exists, None otherwise
        """
        seasonal_map_path = os.path.join("maps", "seasonal", season.value, f"{base_map_name}.json")
        
        if os.path.exists(seasonal_map_path):
            logger.info(f"Found seasonal map: {seasonal_map_path}")
            return seasonal_map_path
        
        return None
    
    def list_available_seasonal_maps(self, season: SeasonalEvent) -> List[str]:
        """
        List all available seasonal maps for a given season.
        
        Args:
            season: The seasonal event
            
        Returns:
            List of available seasonal map names (without .json extension)
        """
        seasonal_maps_dir = os.path.join("maps", "seasonal", season.value)
        
        if not os.path.exists(seasonal_maps_dir):
            return []
        
        seasonal_maps = []
        for filename in os.listdir(seasonal_maps_dir):
            if filename.endswith(".json"):
                map_name = filename[:-5]  # Remove .json extension
                seasonal_maps.append(map_name)
        
        return sorted(seasonal_maps)
    
    def get_seasonal_info(self, season: SeasonalEvent) -> Dict:
        """
        Get comprehensive information about a seasonal event.
        
        Args:
            season: The seasonal event
            
        Returns:
            Dictionary with seasonal information
        """
        theme = self.get_seasonal_theme(season)
        return {
            "name": self.get_seasonal_display_name(season),
            "value": season.value,
            "dates": self.seasonal_dates.get(season, []),
            "theme": theme.get("theme", ""),
            "description": theme.get("description", ""),
            "colors": theme.get("colors", []),
            "maps_available": self.list_available_seasonal_maps(season),
            "content_available": self.is_seasonal_content_available(season, "map")
        }
    
    def create_seasonal_directories(self):
        """Create the directory structure for seasonal content."""
        base_seasonal_dir = os.path.join("maps", "seasonal")
        os.makedirs(base_seasonal_dir, exist_ok=True)
        
        for season in SeasonalEvent:
            seasonal_dir = os.path.join(base_seasonal_dir, season.value)
            os.makedirs(seasonal_dir, exist_ok=True)
            logger.info(f"Created seasonal directory: {seasonal_dir}")
    
    def get_next_seasonal_event(self, from_date: Optional[datetime.date] = None) -> Tuple[SeasonalEvent, datetime.date]:
        """
        Get the next upcoming seasonal event.
        
        Args:
            from_date: Date to calculate from, uses today if None
            
        Returns:
            Tuple of (SeasonalEvent, date of event)
        """
        start_date = from_date or datetime.date.today()
        year = start_date.year
        
        # Create list of all seasonal events with their dates for this year
        events_this_year = []
        for season, dates in self.seasonal_dates.items():
            # Use the primary date (first in list) for each season
            primary_date = dates[0]
            event_date = datetime.date(year, primary_date[0], primary_date[1])
            events_this_year.append((season, event_date))
        
        # Sort by date
        events_this_year.sort(key=lambda x: x[1])
        
        # Find next event after start_date
        for season, event_date in events_this_year:
            if event_date > start_date:
                return season, event_date
        
        # If no events left this year, return first event of next year
        next_year_event = events_this_year[0]
        next_year_date = datetime.date(year + 1, next_year_event[1].month, next_year_event[1].day)
        return next_year_event[0], next_year_date


# Global instance for easy access
seasonal_manager = SeasonalEventManager()


def get_active_season() -> Optional[SeasonalEvent]:
    """Convenience function to get the currently active seasonal event."""
    return seasonal_manager.get_active_season()


def get_seasonal_map_path(base_map_name: str, season: Optional[SeasonalEvent] = None) -> Optional[str]:
    """
    Convenience function to get seasonal map path.
    
    Args:
        base_map_name: Base map name
        season: Seasonal event, uses active season if None
        
    Returns:
        Path to seasonal map or None
    """
    if season is None:
        season = get_active_season()
    
    if season is None:
        return None
    
    return seasonal_manager.get_seasonal_map_path(base_map_name, season)