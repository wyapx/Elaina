class InternalError(Exception):
    pass


class ResourceBrokenError(InternalError, ConnectionError):
    pass

