from typing import TypeVar, Callable, Any
from sastac.util.logger import logger

T = TypeVar('T')

def retry(
    func: Callable[..., T],
    max_attempts: int,
    action_name: str,
    *args: Any,
    **kwargs: Any
) -> T | None:
    """
    Executes a function with retry logic.
    
    Args:
        func: The function to execute.
        max_attempts: The maximum number of attempts allowed.
        action_name: The name of the action being performed (for logging).
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function if successful, or None if all attempts fail.
    """
    attempts = 0
    while attempts < max_attempts:
        exc = None
        try:
            logger.debug(f"{action_name} (attempt: {attempts + 1} of {max_attempts})")
            result = func(*args, **kwargs)
            logger.debug(f"Successfully completed: {action_name}")
            return result
        except Exception as e:
            logger.debug(f"Failed to execute step {action_name} with error {e}")
            attempts += 1
            exc = e
    
    raise exc
