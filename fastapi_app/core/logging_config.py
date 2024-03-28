import logging
import os
import sys
from types import FrameType
from typing import cast

import loguru
import uvicorn

from fastapi_app.core.logging_constant import LOG_FILE_PATH, LOG_HANDLER, LOGGING_LEVEL
from fastapi_app.core.logging_formatter import ColoredJSONLogFormatter, JSONLogFormatter
from fastapi_app.core.settings import settings


class ConsoleLogger(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Get corresponding Loguru level if it exists
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1
        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored_json": {
            "()": ColoredJSONLogFormatter,
        },
        "json": {
            "()": JSONLogFormatter,
        },
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        },
    },
    "handlers": {
        "json": {
            # NOTE: colored json log
            # "formatter": "colored_json",
            "formatter": "colored",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "intercept": {
            "()": ConsoleLogger,
        },
        "file_handler": {
            "level": "INFO",
            # NOTE: FileHandler #
            # NOTE: 默认生成 logs.log.1, logs.log.2, logs.log.3, ...
            # "filename": LOG_FILE_PATH,
            # "class": "logging.FileHandler",
            # NOTE: TimedRotatingFileHandler #
            # FIXME: 按日期生成
            # "filename": f"logs/log_%Y-%m-%d.log",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "formatter": "json",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": 30,
            # NOTE: RotatingFileHandler #
            "filename": LOG_FILE_PATH,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 30,
        },
    },
    "loggers": {
        "main": {
            "handlers": LOG_HANDLER,
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": LOG_HANDLER,
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": LOG_HANDLER,
            "level": "ERROR",
            "propagate": False,
        },
    },
}

log_config = uvicorn.config.LOGGING_CONFIG

if (
    settings.PROMETHEUS_ENABLE == "true"
    or os.environ.get("PROMETHEUS_ENABLE") == "true"
):
    log_config["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"  # noqa: E501
    )
