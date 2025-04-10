"""Project-wide logging setup."""

import logging
import sys
from core.config import settings

def setup_logging():
    """
    Configures the root logger for the application based on settings.
    """
    log_level = settings.LOG_LEVEL
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Avoid adding multiple handlers if setup_logging is called again
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Create formatter and add it to the handler
        formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler.setFormatter(formatter)

        # Add the handler to the root logger
        logger.addHandler(console_handler)

    logging.info(f"Logging configured with level: {log_level}")

# --- Example Usage (Optional - can be removed) ---
# if __name__ == "__main__":
#     setup_logging()
#     logging.debug("This is a debug message.")
#     logging.info("This is an info message.")
#     logging.warning("This is a warning message.")
#     logging.error("This is an error message.")
#     logging.critical("This is a critical message.")
#
#     # Example of getting a specific logger
#     my_module_logger = logging.getLogger("my_module")
#     my_module_logger.info("Log message from my_module")
