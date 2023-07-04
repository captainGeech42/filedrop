import json

from flask import Response


class _ApiResp(Response):
    """A response from the API routes."""

    def __init__(self, code: int, status: str, msg: str | None = None, headers: dict | None = None, **kwargs):
        j: dict[str, str | dict] = {
            "status": status,
        }

        if msg is not None:
            j["msg"] = msg

        if kwargs is not None:
            j["data"] = kwargs

        super().__init__(status=code, headers=headers, content_type="application/json", response=json.dumps(j))


class ApiError(_ApiResp):
    """An error response from the API."""

    def __init__(self, msg: str, code=400, **kwargs):
        super().__init__(code, "error", msg, **kwargs)


class ApiSuccess(_ApiResp):
    """An success response from the API."""

    def __init__(self, msg: str | None = None, headers: dict | None = None, code=200, **kwargs):
        super().__init__(code, "success", msg=msg, headers=headers, **kwargs)
