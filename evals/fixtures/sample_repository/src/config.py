"""Application configuration loading."""

from dataclasses import dataclass


@dataclass
class Settings:
    """Loads runtime settings for the sample app."""

    model_name: str = "demo-model"
    max_steps: int = 5
