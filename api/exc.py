class ServiceError(Exception):
    """Base class for error that may raise during service execution"""

    def __init__(self, msg, *args: object) -> None:
        self.msg = msg
        super().__init__(*args)

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.msg}"

    def __repr__(self) -> str:
        _repr = super().__repr__()
        return f"{_repr}: msg={self.msg}"


class ClientError(ServiceError):
    """Error that may raise due to client input"""


class InternalError(ServiceError):
    """Error that may be related with internal server issues
    this error should not be exposed to client, messages may or
    may not have details about internal implementations"""

    def __init__(self, msg, internal_exc, *args: object) -> None:
        self.internal_exc = internal_exc
        super().__init__(msg, *args)
