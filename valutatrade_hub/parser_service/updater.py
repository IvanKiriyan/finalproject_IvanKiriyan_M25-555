from __future__ import annotations

import logging
from typing import Any

from valutatrade_hub.core.utils import utcnow_iso
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import RatesStorage

#Класс для работы с процессами обновлений
class RatesUpdater:
    def __init__(self, clients: list[BaseApiClient], storage: RatesStorage) -> None:
        self._clients = clients
        self._storage = storage
        self._logger = logging.getLogger(__name__)

    def run_update(self) -> dict[str, Any]:
        self._logger.info("Начинаем обновление...")

        merged_pairs: dict[str, dict[str, Any]] = {}
        history_records: list[dict[str, Any]] = []
        ts = utcnow_iso()

        for client in self._clients:
            name = type(client).__name__
            try:
                data = client.fetch_rates()
                self._logger.info("Извлекаем из %s... OK (%s rates)", name, len(data))
                for pair, obj in data.items():
                    merged_pairs[pair] = obj
                    history_records.append(
                        {
                            "id": f"{pair}_{ts}",
                            "from_currency": pair.split("_", 1)[0],
                            "to_currency": pair.split("_", 1)[1],
                            "rate": obj.get("rate"),
                            "timestamp": obj.get("updated_at"),
                            "source": obj.get("source"),
                            "meta": {"client": name},
                        }
                    )
            except Exception as e:
                self._logger.error("Ошибка %s: %s", name, str(e))

        self._logger.info("Записываем данные %s в data/rates.json...", len(merged_pairs))
        self._storage.write_snapshot(merged_pairs)
        self._storage.append_history(history_records)

        return {"total": len(merged_pairs), "last_refresh": ts}