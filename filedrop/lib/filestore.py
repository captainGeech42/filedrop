import filedrop.lib.database as f_db

DEFAULT_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10gb


class Filestore:
    """Manager for an on-disk filestore"""

    def __init__(self, db: f_db.Database, root_path: str, max_size: int = DEFAULT_MAX_SIZE):
        self._db = db
        self._root_path = root_path
        self._max_size = max_size

    def a(self):
        """a"""

    def b(self):
        """b"""
