class InternalError(Exception):
    pass


class ResourceBrokenError(InternalError, ConnectionError):
    pass


class BotMutedError(InternalError):
    pass


class PermissionDeniedError(InternalError):
    pass
 
