import logging
import os

import uvicorn
from fastapi import FastAPI

# from opentelemetry.propagate import inject
from utils import PrometheusMiddleware, is_running_in_docker, metrics, setting_otlp

APP_NAME = os.environ.get("APP_NAME", "app")
EXPOSE_PORT = os.environ.get("EXPOSE_PORT", 8000)
# NOTE: 如果是通过 docker-compose 启动，需要使用服务名作为 hostname
OTLP_GRPC_ENDPOINT = os.environ.get(
    "OTLP_GRPC_ENDPOINT",
    "http://tempo:4317" if is_running_in_docker() else "http://localhost:4317",
)

TARGET_ONE_HOST = os.environ.get("TARGET_ONE_HOST", "app-b")
TARGET_TWO_HOST = os.environ.get("TARGET_TWO_HOST", "app-c")

app = FastAPI()

# Setting metrics middleware
app.add_middleware(PrometheusMiddleware, app_name=APP_NAME)
app.add_route("/metrics", metrics)

# Setting OpenTelemetry exporter
setting_otlp(app, APP_NAME, OTLP_GRPC_ENDPOINT)


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


@app.get("/")
async def root():
    logging.info("root endpoint")
    app_message = os.environ.get("APP_MESSAGE", "Hello")

    return {"message": app_message}


if __name__ == "__main__":
    """
    asctime: The time of creation of the LogRecord (formatted as "2003-07-08 16:49:45,896")
    levelname: The textual representation of the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    name: The name of the logger used to log the call.
    filename: The filename portion of pathname.
    lineno: The line number portion of pathname.
    message: The logged message, computed as msg % args. This is set when Formatter.format() is invoked.
    
    # NOTE: OpenTelemetry attributes
    otelTraceID: The trace ID of the span.
    otelSpanID: The span ID of the span.
    otelServiceName: The service name of the span.
    """
    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    # NOTE: 每次请求产生 2 条日志，一条是 access 日志，一条是 info 日志
    # 2024-03-28 15:41:29,470 INFO [root] [main.py:40] [trace_id=16546c4ea2db3b68f472c8e2841d4a64 span_id=451ec8acd7a42309 resource.service.name=app trace_sampled=True] - root endpoint
    # 2024-03-28 15:41:29,475 INFO [uvicorn.access] [h11_impl.py:477] [trace_id=16546c4ea2db3b68f472c8e2841d4a64 span_id=388428c9bf6688eb resource.service.name=app] - 127.0.0.1:39542 - "GET / HTTP/1.1" 200
    log_config["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    )
    # NOTE: 2024-03-28 15:15:07,485 INFO [uvicorn.access] [h11_impl.py:477] - 127.0.0.1:41882 - "GET / HTTP/1.1" 200
    # log_config["formatters"]["access"]["fmt"] = (
    #     "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    # )
    # NOTE: "main:app" 或 "fastapi_app.main:app" 都可以
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
