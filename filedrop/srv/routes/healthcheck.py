# pylint: disable=missing-function-docstring

from flask import Blueprint

bp = Blueprint("healthcheck", __name__)


@bp.get("/healthcheck")
def healthcheck():
    return {"status": "good"}
