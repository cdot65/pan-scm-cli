"""Logging utilities for SCM CLI."""

import logging
from typing import Dict, List, Optional

# Map of level names to logging levels
LOG_LEVELS: Dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

def set_log_level(level_name: str, module: Optional[str] = None) -> bool:
    """Set the log level for the entire application or a specific module.
    
    Args:
        level_name: The log level name (debug, info, warning, error, critical)
        module: Optional module name (e.g., "scm_cli.cli.object")
    
    Returns:
        True if the log level was set successfully, False otherwise
    """
    # Normalize level name
    level_name = level_name.lower()
    
    # Check if the level name is valid
    if level_name not in LOG_LEVELS:
        return False
    
    # Get the actual log level
    level = LOG_LEVELS[level_name]
    
    # Set the log level for the root logger or a specific module
    logger_name = "scm_cli" if not module else module
    if not module or module.startswith("scm_cli"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
        # If we're setting the root logger level, also update all handlers
        if logger_name == "scm_cli":
            for handler in logger.handlers:
                handler.setLevel(level)
                
        return True
    else:
        return False

def get_log_levels() -> List[Dict[str, str]]:
    """Get current log levels for all loggers in the scm_cli hierarchy.
    
    Returns:
        List of dictionaries with logger name and current level
    """
    result = []
    
    # Get the root logger
    root_logger = logging.getLogger("scm_cli")
    
    # Add the root logger
    result.append({
        "name": "scm_cli",
        "level": _level_to_name(root_logger.level)
    })
    
    # Get all loggers from the logging module
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict
               if name.startswith("scm_cli.")]
    
    # Add the actual level for each logger
    for logger in loggers:
        # Only include loggers that have their level explicitly set
        if logger.level != 0:  # 0 means not set
            result.append({
                "name": logger.name,
                "level": _level_to_name(logger.level)
            })
    
    return result

def _level_to_name(level: int) -> str:
    """Convert a logging level to its name.
    
    Args:
        level: The logging level
    
    Returns:
        The name of the logging level
    """
    for name, value in LOG_LEVELS.items():
        if value == level:
            return name
    return "unset"  # This should never happen