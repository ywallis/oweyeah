import logging

logger = logging.getLogger("fastapi")


fmt = logging.Formatter("%(name)s: %(asctime)s | %(levelname)s | %(message)s")

logger.handlers.clear()

file_handler = logging.FileHandler("app.log")

file_handler.setFormatter(fmt)

logger.handlers = [file_handler]

logger.setLevel(logging.INFO)
"""
logging.Logger: configured logger for the application.
"""
