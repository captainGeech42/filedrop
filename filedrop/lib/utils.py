import binascii
import uuid

# bytestr length of the uuid
UUID_LENGTH = 16


def gen_uuid() -> bytes:
    """Generate a new UUID value."""

    return uuid.uuid4().bytes


def hexstr(bytz: bytes) -> str:
    """Convert bytes to a hex string"""

    return binascii.hexlify(bytz).decode("utf-8")


def unhexstr(hexs: str) -> bytes | None:
    """Convert a hex string to bytes, or return None if not a valid hexstr"""

    try:
        return binascii.unhexlify(hexs)
    except binascii.Error:
        return None
