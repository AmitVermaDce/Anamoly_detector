"""Custom exception classes for the application."""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ConfigurationError(ApplicationException):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class DatabaseConnectionError(ApplicationException):
    """Raised when a database connection cannot be established."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class QueryExecutionError(ApplicationException):
    """Raised when a SQL query fails to execute."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class QueryNotFoundError(ApplicationException):
    """Raised when a requested named query is not found in the SQL file."""

    def __init__(self, query_name: str) -> None:
        super().__init__(f"Query '{query_name}' not found.", status_code=404)


class DataProcessingError(ApplicationException):
    """Raised when data transformation or processing fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class DetectionAlgorithmError(ApplicationException):
    """Raised when an anomaly detection algorithm fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class InvalidAlgorithmError(ApplicationException):
    """Raised when an unsupported detection algorithm is requested."""

    def __init__(self, algorithm: str) -> None:
        super().__init__(f"Unsupported detection algorithm: '{algorithm}'.", status_code=400)
