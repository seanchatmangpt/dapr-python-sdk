import functools
from datetime import datetime, timezone
from loguru import logger


def log_timing_and_docstring(func):
    """
    Decorator that logs the function's docstring, start time, and end time in Zulu time.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now(timezone.utc)
        start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"Starting function '{func.__name__}' at {start_time_str}")
        print(f"Docstring: {func.__doc__}")

        result = func(*args, **kwargs)

        end_time = datetime.now(timezone.utc)
        end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"Ending function '{func.__name__}' at {end_time_str}")

        return result

    return wrapper
