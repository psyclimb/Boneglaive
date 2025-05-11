#!/usr/bin/env python3
"""
Event system for component communication.
Provides a pub/sub pattern for decoupled component interactions.
"""
from enum import Enum, auto
from typing import Dict, List, Callable, Any


class EventType(Enum):
    """Enumeration of event types in the system."""
    # Game state events
    GAME_INITIALIZED = auto()
    TURN_STARTED = auto()
    TURN_ENDED = auto()
    GAME_OVER = auto()
    
    # UI events
    UNIT_SELECTED = auto()
    UNIT_DESELECTED = auto()
    CURSOR_MOVED = auto()
    MODE_CHANGED = auto()
    
    # Unit action events
    MOVE_PLANNED = auto()
    MOVE_EXECUTED = auto()
    MOVE_CANCELLED = auto()
    ATTACK_PLANNED = auto()
    ATTACK_EXECUTED = auto()
    ATTACK_CANCELLED = auto()
    
    # Multiplayer events
    PLAYER_CHANGED = auto()
    
    # UI component events
    MESSAGE_LOGGED = auto()
    HELP_TOGGLED = auto()
    LOG_TOGGLED = auto()
    CHAT_TOGGLED = auto()
    DEBUG_TOGGLED = auto()
    
    # UI update events
    UI_REDRAW_REQUESTED = auto()
    
    # Message events
    MESSAGE_DISPLAY_REQUESTED = auto()
    
    # Mode transition request events
    SELECT_MODE_REQUESTED = auto()
    MOVE_MODE_REQUESTED = auto()
    ATTACK_MODE_REQUESTED = auto()
    SKILL_MODE_REQUESTED = auto()
    TELEPORT_MODE_REQUESTED = auto()
    CANCEL_REQUESTED = auto()
    
    # Setup phase events
    SETUP_PHASE_STARTED = auto()
    SETUP_PHASE_PLAYER_CHANGED = auto()
    UNIT_PLACED = auto()
    SETUP_PHASE_COMPLETED = auto()
    
    # Skill effect events
    EFFECT_EXPIRED = auto()


class EventData:
    """
    Base class for event data.
    Events can be published with any data object, but using structured
    event data classes helps with type checking and documentation.
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class EventManager:
    """
    Event manager for the pub/sub system.
    
    Components can subscribe to events and publish events through this central manager.
    This enables decoupled communication between components.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one event manager exists."""
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._subscribers = {}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event manager if not already initialized."""
        if not self._initialized:
            self._subscribers = {event_type: [] for event_type in EventType}
            self._initialized = True
    
    def subscribe(self, event_type: EventType, callback: Callable[[EventType, Any], None]):
        """
        Subscribe to an event.
        
        Args:
            event_type: The event type to subscribe to
            callback: The function to call when the event is published.
                     Should accept event_type and event_data parameters.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[EventType, Any], None]):
        """
        Unsubscribe from an event.
        
        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
    
    def publish(self, event_type: EventType, event_data: Any = None):
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: The type of event to publish
            event_data: The data to pass to subscribers (optional)
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_type, event_data)
                except Exception as e:
                    # Log error but continue with other subscribers
                    from boneglaive.utils.debug import logger
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    def clear_all_subscribers(self):
        """Clear all subscribers (useful for testing or resetting)."""
        self._subscribers = {event_type: [] for event_type in EventType}


# Specific event data classes

class UnitSelectedEventData(EventData):
    """Data for UNIT_SELECTED events."""
    def __init__(self, unit, position):
        super().__init__(unit=unit, position=position)


class UnitDeselectedEventData(EventData):
    """Data for UNIT_DESELECTED events."""
    def __init__(self, unit):
        super().__init__(unit=unit)


class CursorMovedEventData(EventData):
    """Data for CURSOR_MOVED events."""
    def __init__(self, position, previous_position=None):
        super().__init__(position=position, previous_position=previous_position)


class ModeChangedEventData(EventData):
    """Data for MODE_CHANGED events."""
    def __init__(self, new_mode, previous_mode=None):
        super().__init__(new_mode=new_mode, previous_mode=previous_mode)


class MoveEventData(EventData):
    """Data for MOVE_PLANNED and MOVE_EXECUTED events."""
    def __init__(self, unit, from_position, to_position):
        super().__init__(unit=unit, from_position=from_position, to_position=to_position)


class AttackEventData(EventData):
    """Data for ATTACK_PLANNED and ATTACK_EXECUTED events."""
    def __init__(self, attacker, target, damage=None):
        super().__init__(attacker=attacker, target=target, damage=damage)


class TurnEventData(EventData):
    """Data for TURN_STARTED and TURN_ENDED events."""
    def __init__(self, player, turn_number):
        super().__init__(player=player, turn_number=turn_number)


class PlayerChangedEventData(EventData):
    """Data for PLAYER_CHANGED events."""
    def __init__(self, player, is_local_player):
        super().__init__(player=player, is_local_player=is_local_player)


class GameOverEventData(EventData):
    """Data for GAME_OVER events."""
    def __init__(self, winner):
        super().__init__(winner=winner)


class MessageDisplayEventData(EventData):
    """Data for MESSAGE_DISPLAY_REQUESTED events."""
    def __init__(self, message, message_type=None, log_message=True):
        super().__init__(message=message, message_type=message_type, log_message=log_message)


class UIRedrawEventData(EventData):
    """Data for UI_REDRAW_REQUESTED events."""
    def __init__(self, show_cursor=True, show_selection=True, show_attack_targets=True):
        super().__init__(
            show_cursor=show_cursor, 
            show_selection=show_selection,
            show_attack_targets=show_attack_targets
        )


class UnitPlacedEventData(EventData):
    """Data for UNIT_PLACED events."""
    def __init__(self, unit, position, player, units_remaining):
        super().__init__(
            unit=unit,
            position=position,
            player=player,
            units_remaining=units_remaining
        )


class SetupPhaseEventData(EventData):
    """Data for SETUP_PHASE_STARTED and SETUP_PHASE_PLAYER_CHANGED events."""
    def __init__(self, player, units_remaining):
        super().__init__(player=player, units_remaining=units_remaining)


class EffectExpiredEventData(EventData):
    """Data for EFFECT_EXPIRED events."""
    def __init__(self, skill_name):
        super().__init__(skill_name=skill_name)


# Helper function to get event manager instance
def get_event_manager() -> EventManager:
    """Get the global event manager instance."""
    return EventManager()