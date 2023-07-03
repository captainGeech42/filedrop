import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime

from Crypto.Random import get_random_bytes

import filedrop.lib.exc as f_exc
import filedrop.lib.utils as f_utils

log = logging.getLogger(__name__)


@dataclass
class User:
    """A representation of a user from the database."""

    uuid: bytes
    username: str
    password_hash: bytes | None = None
    salt: bytes | None = None
    enabled: bool = True
    is_anon: bool = False

    @classmethod
    def gen_salt(cls) -> bytes:
        """Generate a salt value"""

        return get_random_bytes(16)

    @classmethod
    def hash_pw(cls, password: str | bytes, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """Hash the password using scrypt. Returns the (hash, salt)"""

        if isinstance(password, str):
            password = password.encode()

        if not salt:
            salt = cls.gen_salt()

        n = 2**14
        r = 8
        p = 1

        h = hashlib.scrypt(password=password, salt=salt, n=n, r=r, p=p)
        del password

        return (h, salt)

    @staticmethod
    def new(username, password) -> "User":
        """Construct a new user object"""

        (h, salt) = User.hash_pw(password)
        del password

        return User(uuid=f_utils.gen_uuid(), username=username, password_hash=h, salt=salt)

    def check_password(self, password: str) -> bool:
        """Check if the provided password is valid for this user"""

        if self.is_anon:
            log.debug("%s is anonymous, assuming valid password", self)
            return True

        if not self.password_hash is not None and self.salt is not None:
            raise f_exc.InvalidState(f"Can't check the password, don't have valid params for {self}")

        (h, _) = self.hash_pw(password, self.salt)
        del password

        return h == self.password_hash

    def update_password(self, password: str):
        """Replace the hash+salt for the new password."""

        (self.password_hash, self.salt) = self.hash_pw(password)
        del password

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def __str__(self) -> str:
        return repr(self)


@dataclass
# pylint: disable-next=too-many-instance-attributes
class File:
    """A representation of a file upload from the database."""

    uuid: bytes
    name: str
    path: str
    size: int
    file_hash: str
    username: str
    expiration_time: datetime | None = None
    max_downloads: int | None = None
    uploaded_at: datetime | None = None

    @staticmethod
    # pylint: disable-next=too-many-arguments
    def new(
        name: str,
        path: str,
        size: int,
        file_hash: str,
        username: str,
        expiration_time: datetime | None = None,
        max_downloads: int | None = None,
        uploaded_at: datetime | None = None,
    ) -> "File":
        """Generate a new File object"""

        return File(
            uuid=f_utils.gen_uuid(),
            name=name,
            path=path,
            size=size,
            file_hash=file_hash,
            username=username,
            expiration_time=expiration_time,
            max_downloads=max_downloads,
            uploaded_at=uploaded_at,
        )

    def __repr__(self) -> str:
        return f"<File {self.name} [{self.file_hash[:8]}...{self.file_hash[-8:]}, {self.size} bytes] - user {self.username}>"

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, rhs) -> bool:
        if not isinstance(rhs, File):
            return False

        return (
            self.uuid == rhs.uuid
            and self.name == rhs.name
            and self.path == rhs.path
            and self.size == rhs.size
            and self.file_hash == rhs.file_hash
            and self.username == rhs.username
            and self.expiration_time == rhs.expiration_time
            and self.max_downloads == rhs.max_downloads
        )
