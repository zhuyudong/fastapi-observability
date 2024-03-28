import json
import logging
import uuid
from datetime import datetime

import stackprinter

from fastapi_app.core.globals import g
from fastapi_app.core.logging_constant import COLORS, LEVEL_TO_NAME
from fastapi_app.core.logging_schema import BaseJSONLogSchema
from fastapi_app.core.settings import settings
from fastapi_app.utils import is_ip_start


class ColoredJSONLogFormatter(logging.Formatter):
    """
    custom class-formatter for writing logs to json
    """

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        """
        Formating LogRecord to json

        :param record: logging.LogRecord
        :return: json string
        <LogRecord: main, 20, /home/qj00304/Code/pegasus/portal_backend_cloud/portal/app/core/ultimate_logging.py, 159, "127.0.0.1:41742 - 2024-03-12T19:09:26.026217 d8cc300ce77a4454a3db6487640f0f66 "POST   http://localhost:8000/api/v1/auth/login HTTP/1.1" 200 "OK" 61ms">
        """
        log_object: dict = self._format_log_object(record)
        # return json.dumps(log_object, ensure_ascii=False)
        log_json = json.dumps(log_object, ensure_ascii=False)
        log_level_color = COLORS.get(record.levelname, COLORS["RESET"])
        return f"{log_level_color}{log_json}{COLORS['RESET']}"

    @staticmethod
    def _format_log_object(record: logging.LogRecord) -> dict:
        now = (
            datetime.fromtimestamp(record.created)
            .astimezone()
            .replace(microsecond=0)
            .isoformat()
        )
        message = record.getMessage()
        duration = record.duration if hasattr(record, "duration") else record.msecs
        if hasattr(g, "trace_id"):
            trace_id = g.trace_id
        else:
            trace_id = str(uuid.uuid4().hex)
            g.trace_id = trace_id
        json_log_fields = BaseJSONLogSchema(
            trace_id=trace_id,
            thread=record.process,
            timestamp=now,
            level_name=LEVEL_TO_NAME[record.levelno],
            message=message,
            source_log=record.name,
            duration=duration,
            app_name=settings.PROJECT_NAME,
            app_version=settings.API_VERSION,
            app_env=settings.ENVIRONMENT,
        )

        if hasattr(record, "props"):
            json_log_fields.props = record.props

        if record.exc_info:
            json_log_fields.exceptions = (
                # default library traceback
                # traceback.format_exception(*record.exc_info)
                # stackprinter gets all debug information
                # https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137
                stackprinter.format(
                    record.exc_info,
                    suppressed_paths=[
                        r"lib/python.*/site-packages/starlette.*",
                    ],
                    add_summary=False,
                ).split("\n")
            )

        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        # Pydantic to dict
        json_log_object = json_log_fields.model_dump(
            exclude_unset=True,
            by_alias=True,
        )
        # getting additional fields
        if hasattr(record, "request_json_fields"):
            json_log_object.update(record.request_json_fields)

        return json_log_object


class JSONLogFormatter(logging.Formatter):
    """
    custom class-formatter for writing logs to json
    """

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        """
        Formating LogRecord to json

        :param record: logging.LogRecord
        :return: json string
        """
        log_object: dict = self._format_log_object(record)
        return json.dumps(log_object, ensure_ascii=False)

    @staticmethod
    def _format_log_object(record: logging.LogRecord) -> dict:
        now = (
            datetime.fromtimestamp(record.created)
            .astimezone()
            .replace(microsecond=0)
            .isoformat()
        )
        message = record.getMessage()
        if is_ip_start(message):
            msg = ""
        else:
            msg = message
        duration = record.duration if hasattr(record, "duration") else record.msecs
        if hasattr(g, "trace_id"):
            trace_id = g.trace_id
        else:
            trace_id = str(uuid.uuid4().hex)
            g.trace_id = trace_id
        json_log_fields = BaseJSONLogSchema(
            trace_id=trace_id,
            thread=record.process,
            timestamp=now,
            level_name=LEVEL_TO_NAME[record.levelno],
            message=msg,
            source_log=record.name,
            duration=duration,
            app_name=settings.PROJECT_NAME,
            app_version=settings.API_VERSION,
            app_env=settings.ENVIRONMENT,
        )

        if hasattr(record, "props"):
            json_log_fields.props = record.props

        if record.exc_info:
            json_log_fields.exceptions = (
                # default library traceback
                # traceback.format_exception(*record.exc_info)
                # stackprinter gets all debug information
                # https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137
                stackprinter.format(
                    record.exc_info,
                    suppressed_paths=[
                        r"lib/python.*/site-packages/starlette.*",
                    ],
                    add_summary=False,
                ).split("\n")
            )

        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        # Pydantic to dict
        json_log_object = json_log_fields.model_dump(
            exclude_unset=True,
            by_alias=True,
        )
        # getting additional fields
        if hasattr(record, "request_json_fields"):
            json_log_object.update(record.request_json_fields)

        return json_log_object
