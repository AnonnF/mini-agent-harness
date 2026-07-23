"""Custom exception types for the sample app."""


class SampleAppError(Exception):
    """Base error for the sample application."""


class ConfigError(SampleAppError):
    """Raised when configuration is invalid."""


class RegistryError(SampleAppError):
    """Raised when the tool registry fails."""
