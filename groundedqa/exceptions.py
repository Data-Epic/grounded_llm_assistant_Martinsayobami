"""Custom exceptions for the groundedqa package."""


class GroqAPIError(Exception):
    """Base exception for any error returned by the Groq API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GroqClientError(GroqAPIError):
    """Raised for 4xx responses (except 429, which gets its own class)."""


class GroqServerError(GroqAPIError):
    """Raised for 5xx responses."""


class GroqRateLimitError(GroqAPIError):
    """Raised when a 429 is received and all retries have been exhausted."""


class ResponseParsingError(Exception):
    """Raised when the model's content cannot be parsed/validated as the
    expected structured JSON. Callers should catch this instead of crashing.
    """
