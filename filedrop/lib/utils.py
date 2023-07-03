import binascii
import uuid


def gen_uuid() -> bytes:
    """Generate a new UUID value."""

    return uuid.uuid4().bytes


def hexstr(bytz: bytes) -> str:
    """Convert bytes to a hex string"""

    return binascii.hexlify(bytz).decode("utf-8")
