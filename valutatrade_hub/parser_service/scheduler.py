from __future__ import annotations

import logging
import threading

from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater

#Класс для автоматического обновления курсов валют
class RatesScheduler:
    def __init__(self, interval_seconds: int = 3600) -> None: #Обновление показателей валюты раз - в час, так как у меня количество обращений к апи ограничено
        self._interval = int(interval_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        updater = RatesUpdater(
            clients=[CoinGeckoClient(), ExchangeRateApiClient()],
            storage=RatesStorage(),
        )

        while not self._stop_event.is_set():
            try:
                updater.run_update()
            except Exception as e:
                self._logger.error("Не удалось провести автообновление: %s", str(e))

            self._stop_event.wait(self._interval)