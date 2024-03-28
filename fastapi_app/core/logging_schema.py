from typing import List, Optional, Union

from pydantic import BaseModel


class BaseJSONLogSchema(BaseModel):
    """
    main log in JSON format
    """

    trace_id: str = None
    thread: Union[int, str]
    level_name: str
    message: str
    source_log: str
    timestamp: str  # = Field(..., alias="@timestamp")
    app_name: str
    app_version: str
    app_env: str
    duration: int
    exceptions: Union[List[str], str] = None
    span_id: str = None
    parent_id: str = None

    class Config:
        # 'allow_population_by_field_name' has been renamed to 'populate_by_name'
        # allow_population_by_field_name = True
        populate_by_name = True


class RequestJSONLogSchema(BaseModel):
    """
    schema for request/response answer
    """

    request_uri: str
    request_referer: str
    request_method: str
    request_path: str
    request_host: str
    request_size: int
    request_content_type: str
    request_headers: dict
    request_body: Optional[str] = None
    request_direction: str
    response_status_code: int
    response_size: int
    response_headers: dict
    response_body: Optional[str] = None
    duration: int

    # @field_validator("request_body")
    # @staticmethod
    # def valid_request_body(cls, value):
    #     if isinstance(value, bytes):
    #         try:
    #             value = value.decode()
    #         except UnicodeDecodeError:
    #             value = b"file_bytes"
    #         return value

    #     if isinstance(value, str):
    #         return value
