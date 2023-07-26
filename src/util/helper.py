import time
import os
import random

def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
):
    """Retry a function with exponential backoff."""
 
    def wrapper(*args, **kwargs):
        # Initialize variables
        delay = initial_delay
 
        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)
            # Retry on specific errors
            except Exception as e:
                print("Exception: ", e)
                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())
 
                # Sleep for the delay
                time.sleep(delay)
    return wrapper

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For UNIX-based systems (macOS, Linux)
    else:
        os.system('clear')
