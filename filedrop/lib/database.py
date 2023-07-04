import contextlib
import logging
import os
import sqlite3
from datetime import datetime

from filedrop import ROOT_DIR
import filedrop.lib.exc as f_exc
import filedrop.lib.models as f_models
import filedrop.lib.time as f_time

log = logging.getLogger(__name__)

ANONYMOUS_USERNAME = "anonymous"


class Database:
    """Manager for the local database that handles auth, audit data and file metadata."""

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
            files = os.listdir(self.get_migrations_folder())
            files.sort()

            for f in files:
                if not f.endswith(".sql"):
                    continue

                p = os.path.join(self.get_migrations_folder(), f)

                log.debug("executing migration script: %s", p)

                with open(p, "r", encoding="utf-8") as f:
                    sql = f.read()
                    try:
                        c.executescript(sql)
                    except sqlite3.OperationalError as e:
                        raise f_exc.MigrationFailure(f"failed to execute migration file: {p} - {str(e)}")

        log.info("finished database migrations")
        self._migrated = True

    def close(self):
        """Close the database connection"""

        if self._conn is None:
            raise f_exc.InvalidState("no database connection exists")

        self._conn.commit()
        self._conn.close()
        self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    @property
    def migrated(self):
        """Have the model migrations executed?"""

        return self._migrated

    @classmethod
    def get_migrations_folder(cls):
        """Root folder path containing the migration SQL scripts."""

        return os.path.join(ROOT_DIR, "migrations")

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
                "SELECT uuid, password_hash, salt, enabled, is_anon FROM users WHERE username = ?;",
                (username,),
            )
            r = x.fetchone()

            if r:
                return f_models.User(
                    uuid=r[0], username=username, password_hash=r[1], salt=r[2], enabled=bool(r[3]), is_anon=bool(r[4])
                )

            return None

    def get_user_id(self, username: str) -> int | None:
        """Get the ID for a user from the database. Returns the id if exists, otherwise None."""

        with self.cursor() as c:
            x = c.execute(
                "SELECT id FROM users WHERE username = ?;",
                (username,),
            )
            r = x.fetchone()

            if r:
                return r[0]

            return None

    def add_user(self, user: f_models.User) -> bool:
        """Add a new user to the database. Returns False on failure or duplicate username, else True."""

        with self.cursor() as c:
            try:
                x = c.execute(
                    "INSERT INTO users (uuid, username, password_hash, salt, enabled) VALUES (?, ?, ?, ?, ?);",
                    (user.uuid, user.username, user.password_hash, user.salt, user.enabled),
                )
                return x.rowcount == 1
            except sqlite3.IntegrityError:
                log.debug("duplicate username, can't add to database: %s", user.username)
                return False

    def update_user_pw(self, user: f_models.User) -> bool:
        """Update the hash and salt fields for the specified user. Returns False on failure or no user found, else True."""

        with self.cursor() as c:
            x = c.execute(
                "UPDATE users SET password_hash = ? AND salt = ? WHERE username = ?;",
                (user.password_hash, user.salt, user.username),
            )
            return x.rowcount == 1

    def get_anon_user(self) -> f_models.User | None:
        """Get the anonymous user."""

        return self.get_user("anonymous")

    def add_new_file(self, file: f_models.File) -> datetime | None:
        """Add a new file upload. Returns the upload datetime on success, otherwise None"""

        with self.cursor() as c:
            x = c.execute(
                "INSERT INTO files (uuid, name, size, hash, path, user, expiration_time, max_downloads) VALUES (?, ?, ?, ?, ?, (SELECT id FROM users WHERE username = ?), ?, ?)",
                (
                    file.uuid,
                    file.name,
                    file.size,
                    file.file_hash,
                    file.path,
                    file.username,
                    file.expiration_time,
                    file.max_downloads,
                ),
            )

            if x.rowcount == 1:
                y = c.execute("SELECT created_at FROM files WHERE uuid = ?;", (file.uuid,))
                r = y.fetchall()
                if len(r) != 1:
                    log.error("just uploaded file %s but can't get the created_at value from the database", file)
                    return None

                return f_time.parse_db_timestamp(r[0][0])

            return None

    def get_file(self, uuid: bytes) -> f_models.File | None:
        """Get a file by it's UUID, or None if it doesn't exist."""

        with self.cursor() as c:
            x = c.execute(
                "SELECT name, size, hash, path, users.username, expiration_time, max_downloads, files.created_at FROM files JOIN users ON files.user = users.id WHERE files.uuid = ?;",
                (uuid,),
            )

            r = x.fetchone()

            if r:
                return f_models.File(
                    uuid=uuid,
                    name=r[0],
                    size=r[1],
                    file_hash=r[2],
                    path=r[3],
                    username=r[4],
                    expiration_time=f_time.parse_db_timestamp(r[5]) if r[5] else None,
                    max_downloads=r[6],
                    uploaded_at=f_time.parse_db_timestamp(r[7]),
                )

            return None

    def inc_download_count(self, uuid: bytes) -> bool:
        """Increment the download count for a file. Returns True if the download count was incremented and the file is still under the quota"""

        with self.cursor() as c:
            x = c.execute(
                "UPDATE files SET num_downloads = num_downloads + 1 WHERE uuid = ? AND (num_downloads < max_downloads OR max_downloads IS NULL);",
                (uuid,),
            )

            return x.rowcount == 1
