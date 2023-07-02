import hashlib
import logging
import os
from datetime import datetime

import filedrop.lib.database as f_db
import filedrop.lib.exc as f_exc
import filedrop.lib.models as f_models

DEFAULT_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10gb

log = logging.getLogger(__name__)


class Filestore:
    """Manager for an on-disk filestore"""

    def __init__(self, db: f_db.Database, root_path: str, max_size: int = DEFAULT_MAX_SIZE):
        self._db = db
        self._root_path = root_path.rstrip("/")
        self._max_size = max_size

        # TODO lock the dir and clean it up on destroy

    def _hash_bytes(self, bytz: bytes) -> str:
        """Get the hash of the provided bytes"""

        return hashlib.sha256(bytz, usedforsecurity=False).hexdigest()

    def _gen_path(self, filehash: str, user_id: int) -> str:
        """Generate a path to save the file bytes at."""

        p = os.path.join(self._root_path, str(user_id), filehash[0:2], filehash[2:4], filehash[4:6], filehash[6:])
        if not p.startswith(self._root_path):
            raise f_exc.BadArgs(
                f"the generated file path didn't start with the root directory, something is wrong! generated: {p}, root: {self._root_path}"
            )

        return p

    def _write_bytes(self, path: str, bytz: bytes, overwrite=True) -> bool:
        """
        Save the bytes to the specified path.

        If overwrite is True, a file at that path will be overwritten, otherwise False will be returned if the file already exists.
        """

        # TODO: this is raceable. map path->mutex to lock this code path?
        if not overwrite:
            # make sure the file doesn't exist
            if os.path.exists(path):
                log.debug("file already exists at %s and overwrite=False", path)
                return False

        # make sure the directory exists
        dirn = os.path.dirname(path)
        if not os.path.exists(dirn):
            os.makedirs(dirn, exist_ok=True)

        # save the file
        try:
            with open(path, "wb") as f:
                l = f.write(bytz)
                expected = len(bytz)
                if l != expected:
                    log.error("failed to write file to %s, only wrote %d bytes instead of %d", path, l, expected)
                    return False
                return True
        except PermissionError:
            log.error("failed to write file to %s, permission denied", path)
        except FileNotFoundError:
            log.error("failed to write file to %s, missing upper directories somehow", path)

        return False

    # pylint: disable-next=too-many-arguments
    def save_file(
        self,
        name: str,
        bytz: bytes,
        anon_upload: bool = False,
        username: str | None = None,
        expiration_time: datetime | None = None,
        max_downloads: int | None = None,
    ) -> f_models.File | None:
        """
        Save a file to disk.

        If anon_upload is True, username must be None. Otherwise, the username of the uploader must be specified.
        """

        # validate the combination of arguments
        if anon_upload and (username is not None):
            raise f_exc.BadArgs("anon_upload is True but a username is specified.")

        if not anon_upload and username is None:
            raise f_exc.BadArgs("non-anon upload but no username specified")

        # get the username
        if username is None:
            # doing an anonymous file upload, set the username
            username = f_db.ANONYMOUS_USERNAME

        uid = self._db.get_user_id(username)
        if uid is None:
            raise f_exc.InvalidUser(f"can't save file for user {username}, user doesn't exist")

        # write the file to disk
        h = self._hash_bytes(bytz)
        p = self._gen_path(h, uid)
        if not self._write_bytes(p, bytz):
            return None

        f = f_models.File(
            name=name,
            path=p,
            size=len(bytz),
            hash=h,
            user_id=uid,
            expiration_time=expiration_time,
            max_downloads=max_downloads,
        )

        # save to db
        if not self._db.add_new_file(f):
            log.error("failed to save new file to the database: %s", f)
            return None

        return f
