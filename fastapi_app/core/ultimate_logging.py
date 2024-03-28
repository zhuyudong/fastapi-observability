import json
import logging
import math
import time
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from logging.config import dictConfig
from typing import ClassVar
from uuid import uuid4

from fastapi import Request, Response

# from starlette.background import BackgroundTasks
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import Receive

# TODO
# from user_agents import parse
from fastapi_app.core.globals import g
from fastapi_app.core.logging_config import LOG_CONFIG
from fastapi_app.core.logging_constant import EMPTY_VALUE, PASS_ROUTES
from fastapi_app.core.logging_schema import RequestJSONLogSchema
from fastapi_app.core.settings import settings


class ReceiveProxy:
    """Proxy to starlette.types.Receive.__call__ with caching first receive call.
    https://github.com/tiangolo/fastapi/issues/394#issuecomment-994665859
    """

    receive: Receive
    cached_body: bytes
    _is_first_call: ClassVar[bool] = True

    async def __call__(self):
        # First call will be for getting request body => returns cached result
        if self._is_first_call:
            self._is_first_call = False
            return {
                "type": "http.request",
                "body": self.cached_body,
                "more_body": False,
            }

        return await self.receive()


dictConfig(LOG_CONFIG)

# NOTE: "main" 指向 LOG_CONFIG["loggers"]["main"]
logger = logging.getLogger("main")


class UltimateLoggingMiddleware:
    """Middleware that saves logs to JSON
    The main problem is
    After getting request_body
        body = await request.body()
    Body is removed from requests. I found solution as ReceiveProxy
    """

    @staticmethod
    async def get_protocol(request: Request) -> str:
        protocol = str(request.scope.get("type", ""))
        http_version = str(request.scope.get("http_version", ""))
        if protocol.lower() == "http" and http_version:
            return f"{protocol.upper()}/{http_version}"
        return EMPTY_VALUE

    async def get_request_body(self, request: Request) -> bytes:
        body = await request.body()

        request._receive = ReceiveProxy(receive=request.receive, cached_body=body)
        return body

    def filter_header_and_body(
        self,
        request_headers: dict,
        response_body,
    ) -> tuple:
        # body = json.loads(response_body)
        # if body and body.get("data"):
        #     del body["data"]
        # headers = deepcopy(request_headers)
        # headers.pop("cookie", None)
        # if headers.get("authorization"):
        #     headers.update({"authorization": "****"})
        # return headers, body

        if isinstance(response_body, dict):
            body = json.loads(response_body)
            if "data" in body:
                body.pop("data")
        else:
            body = response_body

        headers = deepcopy(request_headers)

        headers.pop("cookie", None)

        if "authorization" in headers:
            headers["authorization"] = "****"

        return headers, body

    async def __call__(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
        *args,
        **kwargs,
    ):
        # logger.debug(f"Started Middleware: {__name__}")
        start_time = time.time()
        exception_object = None
        state = request.state.__dict__.get("_state")
        if state.get("trace_id", None) is None:
            request.state.trace_id = uuid4().hex
        g.trace_id = request.state.trace_id
        # NOTE: Ignore when requesting static resources
        # request_body = await self.get_request_body(request)
        server: tuple = request.get("server", ("localhost", settings.PORT))
        client: tuple = request.get("client", ("localhost", settings.PORT))
        request_headers: dict = dict(request.headers.items())

        # Response Side
        try:
            response = await call_next(request)
        except Exception as ex:
            # response_body = bytes(http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase.encode())
            # response = Response(
            #     content=response_body,
            #     status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real,
            # )
            exception_object = ex  # noqa
            # response_headers = {}
            # NOTE: JSONLogFormatter.format -> JSONLogFormatter._format_log_object line281 record.exc_info -> print to stdout
            logger.error(msg=f"Exception: {ex}", exc_info=exception_object)
            # OPTIMIZE: https://martinheinz.dev/blog/66
            # stackprinter.show()
            # return response
            raise ex
        else:
            response_headers = dict(response.headers.items())
            response_body = b""

            async for chunk in response.body_iterator:
                response_body += chunk

            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # pass /api/v1/openapi.json, /api/v1/docs, /api/v1/redoc, /api/v1/healthcheck
        if request.url.path in PASS_ROUTES or request.url.path.endswith(
            ".worker.js.map"
        ):
            return response

        duration: int = math.ceil((time.time() - start_time) * 1000)

        # Initializing of json fields
        request_json_fields = RequestJSONLogSchema(
            # Request side
            request_uri=str(request.url),
            request_referer=request_headers.get("referer", EMPTY_VALUE),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            request_content_type=request_headers.get("content-type", EMPTY_VALUE),
            request_headers=request_headers,
            # request_body=request_body,
            request_direction="in",
            # Response side
            response_status_code=response.status_code,
            response_size=int(response_headers.get("content-length", 0)),
            response_headers=response_headers,
            response_body=response_body,
            duration=duration,
        ).model_dump()

        headers, body = self.filter_header_and_body(request_headers, response_body)
        # NOTE: add other logic

        # tasks = BackgroundTasks()
        # tasks.add_task()
        # response.background = tasks
        # message = (
        #     f'{"Error" if exception_object else "Answer"} '
        #     f"code: {response.status_code} "
        #     f'request url: {request.method} "{str(request.url)}" '
        #     f"duration: {duration} ms "
        # )
        timestamp = datetime.fromtimestamp(request.state.start_time).strftime(
            "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        method = request.method
        url = str(request.url)
        method_place = f"{method}{' ' * (7 - len(method))}"
        protocol = await UltimateLoggingMiddleware.get_protocol(request)
        client = f"{request.client.host}:{request.client.port}"
        # INFO     127.0.0.1:59354 - 2024-03-07T18:39:45.425493 77cec0c1556f4a2998a8a01a13ecb6a7 "POST   http://localhost:8000/api/v1/auth/login HTTP/1.1" 200 "OK" 60ms
        message = (
            f'{client} - {timestamp} {request.state.trace_id} "{method_place}{url} {protocol}"'
            f" {response.status_code}"
            f' "{HTTPStatus(response.status_code).phrase}"'
            f" {duration}ms"
        )
        logger.info(
            message,
            extra={
                # NOTE: Injected into format(record: logging.LogRecord) method of the Formatter class
                "request_json_fields": request_json_fields,
                "to_mask": True,
            },
            # exc_info=exception_object,
        )
        return response
