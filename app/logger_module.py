from loguru import logger
import sys
import os

os.makedirs("logs", exist_ok=True)

logger.remove()

logger.add(sys.stderr, level="DEBUG", format="<green>{time}</green> <level>{message}</level>")
logger.add("logs/debug.log", rotation="5 MB", level="DEBUG",
           format="{time} {level} {message}", enqueue=True)
