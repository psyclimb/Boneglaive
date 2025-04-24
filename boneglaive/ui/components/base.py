#!/usr/bin/env python3
from typing import Optional, List, Tuple, Dict, Callable

from boneglaive.utils.event_system import (
    get_event_manager, EventType, EventData
)

# Base class for UI components
class UIComponent:
    """Base class for UI components."""
    
    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        self.renderer = renderer
        self.game_ui = game_ui
        self.event_manager = get_event_manager()
        self._event_subscriptions = []
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """
        Set up event handlers for this component.
        Override this in subclasses to subscribe to events.
        """
        pass
    
    def subscribe_to_event(self, event_type, handler):
        """
        Subscribe to an event and track the subscription.
        
        Args:
            event_type: The event type to subscribe to
            handler: The event handler function
        """
        self.event_manager.subscribe(event_type, handler)
        self._event_subscriptions.append((event_type, handler))
    
    def publish_event(self, event_type, event_data=None):
        """
        Publish an event.
        
        Args:
            event_type: The event type to publish
            event_data: The event data to pass to handlers
        """
        self.event_manager.publish(event_type, event_data)
    
    def unsubscribe_all(self):
        """Unsubscribe from all events this component is subscribed to."""
        for event_type, handler in self._event_subscriptions:
            self.event_manager.unsubscribe(event_type, handler)
        self._event_subscriptions = []
    
    def draw(self):
        """Draw the component."""
        pass
        
    def handle_input(self, key: int) -> bool:
        """Handle input for this component.
        Returns True if the input was handled, False otherwise.
        """
        return False