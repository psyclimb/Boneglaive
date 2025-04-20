#!/usr/bin/env python3
import logging
import os
import sys
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

# Configure logging levels
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

# Debug configuration settings
class DebugConfig:
    def __init__(self):
        self.enabled = False
        self.log_to_file = False
        self.log_level = LogLevel.INFO
        self.perf_tracking = False
        self.show_debug_overlay = False
        self.loggers = {}
        self.performance_data = {}

    def setup_logging(self, module_name: str) -> logging.Logger:
        """Set up logging for a specific module"""
        logger = logging.getLogger(module_name)
        
        # Always reset logger to make sure handlers don't pile up
        logger.setLevel(self.log_level.value)
        
        # Remove any existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters and handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Only log to console if not in curses mode
        # In a curses application, logging to stdout interferes with the UI
        # If log_to_file is True, we'll log to file instead
        if not self.log_to_file:
            # Set up a null handler - we'll only log to file when explicitly enabled
            logger.addHandler(logging.NullHandler())
        
        # File handler (optional)
        if self.log_to_file:
            os.makedirs('logs', exist_ok=True)
            file_handler = logging.FileHandler(f'logs/{module_name}.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Store logger
            self.loggers[module_name] = logger
        
        return logger

    def toggle(self):
        """Toggle debug mode on/off"""
        self.enabled = not self.enabled
        return self.enabled
    
    def toggle_overlay(self):
        """Toggle debug overlay display"""
        self.show_debug_overlay = not self.show_debug_overlay
        return self.show_debug_overlay
    
    def toggle_perf_tracking(self):
        """Toggle performance tracking"""
        self.perf_tracking = not self.perf_tracking
        return self.perf_tracking

# Create a global debug configuration instance
debug_config = DebugConfig()

# Create a root logger for convenience access
logger = logging.getLogger('boneglaive')

# Function timing decorator
def measure_perf(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not debug_config.perf_tracking:
            return func(*args, **kwargs)
        
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        func_name = func.__qualname__
        if func_name not in debug_config.performance_data:
            debug_config.performance_data[func_name] = {
                'calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        # Update stats
        perf_data = debug_config.performance_data[func_name]
        perf_data['calls'] += 1
        perf_data['total_time'] += elapsed_time
        perf_data['avg_time'] = perf_data['total_time'] / perf_data['calls']
        perf_data['min_time'] = min(perf_data['min_time'], elapsed_time)
        perf_data['max_time'] = max(perf_data['max_time'], elapsed_time)
        
        return result
    return wrapper

# Assert functions (will log but not crash in non-debug mode)
def game_assert(condition: bool, message: str, logger: Optional[logging.Logger] = None):
    """Assert a condition and log an error if it fails"""
    if not condition:
        if debug_config.enabled:
            # In debug mode, raise an exception
            assert condition, message
        elif logger:
            # In non-debug mode, log the issue but continue
            logger.error(f"Assertion failed: {message}")

# Get debug overlay information
def get_debug_overlay() -> List[str]:
    """Get debug information to display in the UI overlay"""
    if not debug_config.show_debug_overlay:
        return []
    
    lines = []
    lines.append("=== DEBUG OVERLAY ===")
    
    # Add performance metrics if tracking is enabled
    if debug_config.perf_tracking and debug_config.performance_data:
        lines.append("Performance:")
        # Sort by average time (descending)
        sorted_perf = sorted(
            debug_config.performance_data.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )
        # Show top 5 functions
        for func_name, stats in sorted_perf[:5]:
            lines.append(f"  {func_name}: {stats['avg_time']:.4f}s avg, {stats['calls']} calls")
    
    return lines