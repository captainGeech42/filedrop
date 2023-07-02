import hashlib
import logging
from dataclasses import dataclass

from Crypto.Random import get_random_bytes

import filedrop.lib.exc as f_exc

log = logging.getLogger(__name__)


@dataclass
class File:
    """A representation of a file upload from the database."""

    name: str
    path: str
    size: int


@dataclass
class User:
    """A representation of a user from the database."""

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
    def hash_pw(cls, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
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

        return User(username, h, salt)

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
        return f"<User {self.name}>"

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, rhs) -> bool:
        if not isinstance(rhs, User):
            return False

        return (
            self.username == rhs.username
            and self.password_hash == rhs.password_hash
            and self.salt == rhs.salt
            and self.enabled == rhs.enabled
            and self.is_anon == rhs.is_anon
        )
