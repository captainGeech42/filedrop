"""
Manager for an on-disk filestore
"""

DEFAULT_MAX_SIZE = 10 * 1024 * 1024 * 1024 # 10gb

class Filestore:
    def __init__(self, db, root_path: str, max_size: int = DEFAULT_MAX_SIZE):
        self._root_path = root_path
        self._max_size = max_size
