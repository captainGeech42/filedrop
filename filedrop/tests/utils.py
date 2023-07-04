import contextlib
import copy
import os
import tempfile
import unittest

import flask
import flask.testing

import filedrop.lib.database as f_db
import filedrop.lib.filestore as f_fs
import filedrop.lib.models as f_models
import filedrop.srv as f_srv


class FiledropTest(unittest.TestCase):
    """Unittest wrapper with utilities for managing filedrop resources."""

    @classmethod
    @contextlib.contextmanager
    def getTestDatabase(cls, path=":memory:"):
        """Get a disposable database instance."""

        try:
            with f_db.Database(path=path) as db:
                yield db
        finally:
            pass

    @classmethod
    @contextlib.contextmanager
    def getTestFilestore(cls, db: f_db.Database | None = None, max_size=f_fs.DEFAULT_MAX_SIZE):
        """Get a disposable filestore instance in a tempdir."""

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if db is None:
                    with cls.getTestDatabase() as db:
                        fs = f_fs.Filestore(db, root_path=tmpdir, max_size=max_size)
                        yield fs
                else:
                    fs = f_fs.Filestore(db, root_path=tmpdir, max_size=max_size)
                    yield fs

                # TODO: cleanup via with block once that is implemented
        finally:
            pass

    @classmethod
    @contextlib.contextmanager
    def customEnvVars(cls, vals: dict[str, str]):
        """Define a set of environment variables for the process, and then restore the original environment."""

        _old = copy.deepcopy(os.environ)

        os.environ |= vals
        yield
        os.environ = copy.deepcopy(_old)


class ServerTest(FiledropTest):
    """
    Unittest wrapper with utilities for testing the Flask app.

    The database has a pre-existing user:
        u: user1
        p: hunter2
    """

    app: flask.Flask
    client: flask.testing.Client

    db: f_db.Database
    _db_ctx: contextlib._GeneratorContextManager

    fs: f_fs.Filestore
    _fs_ctx: contextlib._GeneratorContextManager

    @classmethod
    def setUpClass(cls):
        cls._db_ctx = cls.getTestDatabase()
        cls.db = cls._db_ctx.__enter__()

        cls.db.add_user(f_models.User.new("user1", "hunter2"))

        cls._fs_ctx = cls.getTestFilestore(db=cls.db)
        cls.fs = cls._fs_ctx.__enter__()

        cls.app = f_srv.create_app(testing=True, db=cls.db, fs=cls.fs)
        cls.app.config.update({"TESTING": True})

        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls._fs_ctx.__exit__(None, None, None)
        cls._db_ctx.__exit__(None, None, None)
