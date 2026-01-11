from __future__ import annotations

from typing import Any

from valutatrade_hub.core.utils import utcnow_iso
from valutatrade_hub.infra.database import DatabaseManager

#Сохранение итогового проекта
class RatesStorage:
    def __init__(self) -> None:
        self._db = DatabaseManager()

    def write_snapshot(self, pairs: dict[str, dict[str, Any]]) -> None:
        doc = {"pairs": pairs, "last_refresh": utcnow_iso()}
        self._db.save_rates(doc)

    def append_history(self, records: list[dict[str, Any]]) -> None:
        history = self._db.load_history()
        history.extend(records)
        self._db.save_history(history)