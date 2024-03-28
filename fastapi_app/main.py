import logging
import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()


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
    # log_config["formatters"]["access"]["fmt"] = (
    #     "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    # )
    # NOTE: 2024-03-28 15:15:07,485 INFO [uvicorn.access] [h11_impl.py:477] - 127.0.0.1:41882 - "GET / HTTP/1.1" 200
    log_config["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    )
    # NOTE: 如果使用 python fastapi_app/main.py 启动，则是 "main:app", 而不是 fastapi_app.main:app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
