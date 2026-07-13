"""Centralized logging setup for Mini Agent Harness."""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_CONFIGURED = False

def setup_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format=_LOG_FORMAT)
    _CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)