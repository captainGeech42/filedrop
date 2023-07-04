# pylint: disable=missing-function-docstring

import io

from flask import Blueprint, current_app, send_file

import filedrop.lib.models as f_models
import filedrop.lib.utils as f_utils
from filedrop.srv.resps import ApiError, ApiSuccess

bp = Blueprint("apiv1", __name__)


@bp.get("/file/<uuid>")
def file_info(uuid: str):
    uuidb = f_utils.unhexstr(uuid)
    if uuidb is None or len(uuidb) != f_utils.UUID_LENGTH:
        return ApiError("file doesn't exist", uuid=uuid)

    f: f_models.File = current_app.config["db"].get_file(uuidb)
    if f is None:
        return ApiError("file doesn't exist", uuid=uuid)

    return ApiSuccess(name=f.name, size=f.size)


# TODO: auth on this, only the file owner should be able to view this
@bp.get("/file/<uuid>/details")
def file_info_detailed(uuid: str):
    uuidb = f_utils.unhexstr(uuid)
    if uuidb is None or len(uuidb) != f_utils.UUID_LENGTH:
        return ApiError("file doesn't exist", uuid=uuid)

    f: f_models.File = current_app.config["db"].get_file(uuidb)
    if f is None:
        return ApiError("file doesn't exist", uuid=uuid)

    return ApiSuccess(
        name=f.name, size=f.size, uploaded_at=f.uploaded_at, expires_at=f.expiration_time, max_downloads=f.max_downloads
    )


@bp.get("/file/<uuid>/download")
def file_download(uuid: str):
    uuidb = f_utils.unhexstr(uuid)
    if uuidb is None or len(uuidb) != f_utils.UUID_LENGTH:
        return ApiError("file doesn't exist", uuid=uuid)

    f: f_models.File = current_app.config["db"].get_file(uuidb)
    if f is None:
        return ApiError("file doesn't exist", uuid=uuid)

    bytz = current_app.config["fs"].get_file_bytes(uuidb)

    return send_file(io.BytesIO(bytz), as_attachment=True, download_name=f.name)


@bp.post("/file/new")
def file_new():
    pass
