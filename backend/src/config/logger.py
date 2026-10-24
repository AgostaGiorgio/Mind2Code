import logging
import sys

from pythonjsonlogger.jsonlogger import JsonFormatter


def configure_logging(level: str = "INFO") -> None:
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = []
    root.addHandler(handler)
