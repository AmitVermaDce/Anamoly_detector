class ApplicationException(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ConfigurationError(ApplicationException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class DatabaseConnectionError(ApplicationException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class QueryExecutionError(ApplicationException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class QueryNotFoundError(ApplicationException):
    def __init__(self, query_name: str) -> None:
        super().__init__(f"Query '{query_name}' not found.", status_code=404)


class DetectionAlgorithmError(ApplicationException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class InvalidAlgorithmError(ApplicationException):
    def __init__(self, algorithm: str) -> None:
        super().__init__(f"Unsupported detection algorithm: '{algorithm}'.", status_code=400)
