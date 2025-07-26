import logging
import sys
from pythonjsonlogger import jsonlogger


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a JSON logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.propagate = False
    return logger


logger = get_logger(__name__)
