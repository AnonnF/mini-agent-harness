"""Project-specific exception types"""


class MiniAgentError(Exception):
    """Base exception for Mini Agent Harness."""


class ConfigurationError(MiniAgentError):
    """Raised when configuration is missing or invalid."""


class ModelRequestError(MiniAgentError):
    """Raised when an LLM API request fails."""


class ToolExecutionError(MiniAgentError):
    """Raised when a tool execution fails."""
