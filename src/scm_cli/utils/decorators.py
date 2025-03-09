"""Common decorators for SCM CLI."""

import functools
import logging
import time
import tracemalloc
from typing import Any, Callable, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])

def timeit(func: F) -> F:
    """Decorator to measure and log execution time of functions.
    
    This decorator logs the execution time of the decorated function.
    If the execution time exceeds 1.0 second, it will log a warning.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get logger based on the module from which the decorated function is called
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Log timing information
        logger.debug(f"Function {func.__name__} took {duration:.3f} seconds")
        
        # Warn if function takes a long time
        if duration > 1.0:
            logger.warning(
                f"Function {func.__name__} took {duration:.3f} seconds - "
                "performance optimization may be needed"
            )
            
        return result
    
    return cast(F, wrapper)


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """Decorator to retry a function on failure.
    
    This decorator will retry the decorated function up to max_attempts times
    if it raises an exception, with a delay between attempts.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Delay between attempts in seconds (default: 1.0)
        
    Returns:
        The decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger based on the module from which the decorated function is called
            logger = logging.getLogger(func.__module__)
            
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    
                    if attempts < max_attempts:
                        logger.warning(
                            f"Function {func.__name__} failed with error: {str(e)}. "
                            f"Retrying in {delay} seconds (attempt {attempts}/{max_attempts})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {str(e)}"
                        )
            
            # If we get here, all attempts failed
            if last_exception:
                raise last_exception
            return None  # Unreachable but keeps type checker happy
        
        return cast(F, wrapper)
    
    return decorator


def measure_memory(func: F) -> F:
    """Decorator to measure memory usage of a function.
    
    This decorator logs the peak memory usage of the decorated function
    using Python's tracemalloc module.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get logger based on the module from which the decorated function is called
        logger = logging.getLogger(func.__module__)
        
        # Start tracking memory usage
        tracemalloc.start()
        
        # Call the function
        result = func(*args, **kwargs)
        
        # Get memory usage statistics
        current, peak = tracemalloc.get_traced_memory()
        
        # Log memory usage
        logger.debug(f"Function {func.__name__} - Current memory usage: {current / 1024:.2f} KB")
        logger.debug(f"Function {func.__name__} - Peak memory usage: {peak / 1024:.2f} KB")
        
        # Stop tracking
        tracemalloc.stop()
        
        # Warn if function uses a lot of memory
        if peak > 10 * 1024 * 1024:  # 10 MB
            logger.warning(
                f"Function {func.__name__} used {peak / (1024 * 1024):.2f} MB peak memory - "
                "memory optimization may be needed"
            )
            
        return result
    
    return cast(F, wrapper)