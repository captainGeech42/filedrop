"""
Manager for the local database that handles audit data and file metadata.
"""

import contextlib
import logging
import os
import sqlite3
import sys

import filedrop.lib.exc as f_exc
import filedrop.lib.models as f_models

log = logging.getLogger(__name__)


class Database:
    def __init__(self, path=":memory:"):
        self._path = path

        self._conn: sqlite3.Connection | None = None
        self._migrated = False

        self._connect()
        self._migrate()

    def _connect(self):
        """Open a connection to the database"""

        if self._conn is not None:
            raise f_exc.InvalidState("a database connection already exists")

        self._conn = sqlite3.connect(self._path)

    def _migrate(self):
        """Execute the database migrations"""

        if self._conn is None:
            raise f_exc.InvalidState("no database connection exists")

        with self.cursor() as c:
            files = os.listdir(self.migrations_folder)
            files.sort()

            for f in files:
                if not f.endswith(".sql"):
                    continue

                p = os.path.join(self.migrations_folder, f)

                log.debug("executing migration script: %s", p)

                with open(p, "r") as f:
                    sql = f.read()
                    try:
                        c.executescript(sql)
                    except sqlite3.OperationalError as e:
                        raise f_exc.MigrationFailure(f"failed to execute migration file: {p} - {str(e)}")

        log.info("finished database migrations")
        self._migrated = True

    def _close(self):
        """Close the database connection"""

        if self._conn is None:
            raise f_exc.InvalidState("no database connection exists")

        self._conn.commit()
        self._conn.close()
        self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._close()

    @property
    def migrated(self):
        return self._migrated

    @classmethod
    @property
    def migrations_folder(cls):
        """Root folder path containing the migration SQL scripts."""

        return os.path.join(sys.path[1], "filedrop", "migrations")

    @contextlib.contextmanager
    def cursor(self):
        """Get a cursor for the database."""

        if self._conn is None:
            raise f_exc.InvalidState("no database connection exists")

        try:
            c = self._conn.cursor()
            yield c
        finally:
            self._conn.commit()
            c.close()

    def get_user(self, username: str) -> f_models.User | None:
        """Get a user by username from the database, or None if the user does not exist."""

        with self.cursor() as c:
            x = c.execute(
                "select password_hash, salt, enabled, is_anon from users where username = ?;",
                (username,),
            )
            r = x.fetchone()

            if r:
                return f_models.User(username, r[0], r[1], bool(r[2]), bool(r[3]))
            else:
                return None

    def add_user(self, user: f_models.User) -> bool:
        """Add a new user to the database. Returns False on failure or duplicate username, else True."""

        with self.cursor() as c:
            try:
                x = c.execute(
                    "insert into users (username, password_hash, salt, enabled) values (?, ?, ?, ?);",
                    (user.username, user.password_hash, user.salt, user.enabled),
                )
                return x.rowcount == 1
            except sqlite3.IntegrityError:
                log.debug("duplicate username, can't add to database: %s", user.username)
                return False

    def update_user_pw(self, user: f_models.User) -> bool:
        """Update the hash and salt fields for the specified user. Returns False on failure or no user found, else True."""

        with self.cursor() as c:
            x = c.execute(
                "update users set password_hash = ? and salt = ? where username = ?;",
                (user.password_hash, user.salt, user.username),
            )
            return x.rowcount == 1
