import uuid


def gen_uuid() -> bytes:
    """Generate a new UUID value."""

    return uuid.uuid4().bytes
