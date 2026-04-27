from loguru import logger
import sys

def setup_logging(log_level: str = "INFO"):
    logger.remove()
    logger.add(sys.stdout, level=log_level, format="{time} {level} {message}")