#!/usr/bin/env python3
"""Debug configuration, logging setup, and performance measurement."""
import logging
import os
import time
from enum import Enum
from functools import wraps
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
        
        # Suppress console logging by default; stdout noise is unwanted during
        # normal play. When log_to_file is True, log to file instead.
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
