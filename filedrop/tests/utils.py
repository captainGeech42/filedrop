import contextlib
import tempfile
import unittest

import filedrop.lib.database as f_db
import filedrop.lib.filestore as f_fs


class FiledropTest(unittest.TestCase):
    """Unittest wrapper with utilities for managing filedrop resources."""

    @contextlib.contextmanager
    def getTestDatabase(self):
        """Get a disposable database instance."""

        try:
            with f_db.Database() as db:
                yield db
        finally:
            pass

    @contextlib.contextmanager
    def getTestFilestore(self, db: f_db.Database | None = None, max_size=f_fs.DEFAULT_MAX_SIZE):
        """Get a disposable filestore instance in a tempdir."""

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if db is None:
                    with self.getTestDatabase() as db:
                        fs = f_fs.Filestore(db, root_path=tmpdir, max_size=max_size)
                        yield fs
                else:
                    fs = f_fs.Filestore(db, root_path=tmpdir, max_size=max_size)
                    yield fs

                # TODO: cleanup via with block once that is implemented
        finally:
            pass
