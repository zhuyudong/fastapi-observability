import logging
import os

from fastapi_app.core.settings import settings

COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[91m",  # Red
    "RESET": "\033[0m",  # Reset
}

LEVEL_TO_NAME = {
    logging.CRITICAL: "CRITICAL",  # "Critical",
    logging.ERROR: "ERROR",  # "Error",
    logging.WARNING: "WARNING",  # "Warning",
    logging.INFO: "INFO",  # "Information",
    logging.DEBUG: "DEBUG",  # "Debug",
    logging.NOTSET: "TRACE",  # "Trace",
}
# NOTE: logs folder is must exists
LOG_FILE_PATH = os.getcwd() + "/static/logs/logs.log"
# LOG_DIR = os.getcwd() + "/static/logs/"
# LOG_FILE_PATH = LOG_DIR + f"{date.today()}.log"


# NOTE: add log handlers
def handlers(env: str = None, to_file: bool = False):
    if env.lower() in ("prod", "dev"):
        handler = ["json"]
    else:
        handler = ["intercept"]

    if to_file:
        handler.append("file_handler")

    return handler


LOG_HANDLER = handlers(env=settings.ENVIRONMENT, to_file=True)
LOGGING_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO

EMPTY_VALUE = ""
PASS_ROUTES = [
    "/",
    "/metrics",
    f"/api/{settings.API_VERSION}/openapi.json",
    f"/api/{settings.API_VERSION}/docs",
    f"/api/{settings.API_VERSION}/redoc",
    f"/api/{settings.API_VERSION}/healthcheck",
]
