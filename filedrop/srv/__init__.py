import atexit
import logging
import sys

from flask import Flask

import filedrop.lib.config as f_config
import filedrop.lib.database as f_db
import filedrop.lib.filestore as f_fs
from filedrop.srv.routes import BLUEPRINTS

log = logging.getLogger(__name__)

CONFIG = f_config.ConfigLoader(
    "filedrop-server",
    [
        f_config.ConfigOption("fs.path", "Root folder for the filestore", str, required=True),
        f_config.ConfigOption(
            "fs.max", "Max file size that can be uploaded (in bytes)", int, default=f_fs.DEFAULT_MAX_SIZE
        ),
        f_config.ConfigOption("db.path", "Path to store the SQLite database", str, required=True),
        f_config.ConfigOption("debug", "Enable debug logging", bool),
    ],
)


def create_app(
    testing=False, gunicorn=False, db: f_db.Database | None = None, fs: f_fs.Filestore | None = None
) -> Flask:
    """
    Initialize the Flask application.

    - testing: if True, the config is not loaded and requires a db and fs to be specified
    - gunicorn: if True, argv is ignored when loading the config
    - db | fs: use the provided db or fs objects instead of initializing a new one
    """

    # load the config
    if not testing:
        argv = [] if gunicorn else sys.argv[1:]
        if not CONFIG.load_config(argv):
            sys.exit(1)

    # configure logging
    lvl = logging.DEBUG if testing or CONFIG.get_value("debug") else logging.INFO
    logging.basicConfig(level=lvl)

    # init the flask app
    app = Flask(__name__)
    for bp, prefix in BLUEPRINTS:
        log.debug("registering blueprint: %s", bp.name)
        app.register_blueprint(bp, url_prefix=prefix)

    # init the database and filestore
    if db is None:
        db = f_db.Database(CONFIG.get_value("db.path"))

        def db_cleanup():
            db.close()

        atexit.register(db_cleanup)
    if fs is None:
        fs = f_fs.Filestore(db, CONFIG.get_value("fs.path"), CONFIG.get_value("fs.max"))  # type: ignore

    app.config["db"] = db
    app.config["fs"] = fs

    return app
