"""
Possible exceptions that can be raised by filedrop.
"""

class FiledropException(Exception): pass

class InvalidState(FiledropException):
    """The state of an object is invalid for the requested operation."""

class MigrationFailure(FiledropException):
    """The database migrations failed to execute."""