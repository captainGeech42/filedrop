import hashlib
import logging
import os
from datetime import datetime

import filedrop.lib.database as f_db
import filedrop.lib.exc as f_exc
import filedrop.lib.models as f_models
import filedrop.lib.utils as f_utils

DEFAULT_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10gb

log = logging.getLogger(__name__)

# TODO: refactor the read/write stuff to use generators for more effeciency


class Filestore:
    """Manager for an on-disk filestore"""

    def __init__(self, db: f_db.Database, root_path: str, max_size: int = DEFAULT_MAX_SIZE):
        self._db = db
        self._root_path = root_path.rstrip("/")
        self._max_size = max_size

        # TODO lock the dir and clean it up on destroy

    @property
    def root_path(self) -> str:
        """Get the root path of the filestore."""

        return self._root_path

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

    def _read_bytes(self, file: f_models.File) -> bytes | None:
        """Read in the specified file."""

        try:
            with open(file.path, "rb") as f:
                bytz = f.read()
                sz = len(bytz)

                if sz != file.size:
                    log.error(
                        "failed to read file %s, didn't get enough bytes (got %d bytes instead of %d)",
                        file.path,
                        sz,
                        file.size,
                    )
                    return None

                return bytz
        except PermissionError:
            log.error("failed to read file %s, permission denied", file.path)
        except FileNotFoundError:
            log.error("failed to read file %s, file not found", file.path)

        return None

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

        # check size
        sz = len(bytz)
        if sz > self._max_size:
            raise f_exc.FileTooLarge(
                f"can't upload file {name}, too big! max is {self._max_size} bytes, this file is {sz} bytes"
            )

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

        f = f_models.File.new(
            name=name,
            path=p,
            size=sz,
            file_hash=h,
            username=username,
            expiration_time=expiration_time,
            max_downloads=max_downloads,
        )

        # save to db
        if not self._db.add_new_file(f):
            log.error("failed to save new file to the database: %s", f)
            return None

        return f

    def get_file_bytes(self, uuid: bytes, validate_conditions=True) -> bytes | None:
        """
        Get the bytes for a file.

        If validate_conditions is True:
            - the download count is incremented from the database.
            - if an expiration time is set, verify the file is not expired
            - if a max file download count is set, verify there is more quota available

        Returns the file bytes if successfully able to be returned (and preconditions met),
        else None.
        """

        # get the file from the db
        f = self._db.get_file(uuid)
        if f is None:
            return None

        if validate_conditions:
            # check expiration
            if f.expiration_time is not None:
                now = datetime.now()
                if now > f.expiration_time:
                    log.debug("can't download %s, file is expired", f_utils.hexstr(f.uuid))
                    return None

            # check download count
            if not self._db.inc_download_count(f.uuid):
                log.debug("can't download %s, file has exceeded download quota", f_utils.hexstr(f.uuid))
                return None

        # TODO: dec download count if this fails
        # TODO: this whole thing is super raceable too. need some way to do txn locking on the file
        return self._read_bytes(f)
