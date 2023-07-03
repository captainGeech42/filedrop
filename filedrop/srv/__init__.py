import logging

from flask import Flask

import filedrop.lib.config as f_config
from filedrop.srv.routes import BLUEPRINTS

log = logging.getLogger(__name__)

CONFIG = f_config.ConfigLoader(
    "filedrop-server",
    [
        f_config.ConfigOption("port", "TCP port to run the server on", str, required=True),
        f_config.ConfigOption("debug", "Enable debug logging", bool, default=False),
    ],
)


def create_app() -> Flask:
    """Initialize the Flask application."""

    app = Flask(__name__)

    for bp, prefix in BLUEPRINTS:
        log.debug("registering blueprint: %s", bp.name)
        app.register_blueprint(bp, url_prefix=prefix)

    return app
