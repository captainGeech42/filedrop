"""
Possible exceptions that can be raised by filedrop.
"""


class FiledropException(Exception):
    """Base exception for all filedrop exceptions"""


class InvalidState(FiledropException):
    """The state of an object is invalid for the requested operation."""


class MigrationFailure(FiledropException):
    """The database migrations failed to execute."""


class BadArgs(FiledropException):
    """The combination of arguments to the function are invalid."""


class InvalidUser(FiledropException):
    """The user is invalid."""


class FileTooLarge(FiledropException):
    """The size of the file was too large to handle for the current configuration."""
