from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader

#Логирование действий
def setup_logging() -> None:
    settings = SettingsLoader()
    log_dir = Path(settings.get("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "actions.log"

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        fmt="%(levelname)s %(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)