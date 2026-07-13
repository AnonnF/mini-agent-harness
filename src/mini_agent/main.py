"""Mini Agent Harness entry point"""

import mini_agent
from mini_agent.logging_config import get_logger, setup_logging


def main() -> None:
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Mini Agent Harness %s started", mini_agent.__version__)


if __name__ == "__main__":
    main()
