"""Sample application entry point."""

from config import Settings
from registry import ToolRegistry


def main() -> None:
    settings = Settings()
    registry = ToolRegistry()
    print(f"starting app model={settings.model_name}")
    print(f"registered tools={registry.list_names()}")


if __name__ == "__main__":
    main()
