from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader

#Singleton-обертка
class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._settings = SettingsLoader()
            cls._instance = obj
        return cls._instance

    def _ensure_file(self, path: Path, default: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            self.write_json(path, default)

    def read_json(self, path: Path, default: Any) -> Any:
        self._ensure_file(path, default)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)

    def load_users(self) -> list[dict[str, Any]]:
        path = self._settings.path_for("USERS_FILE")
        return self.read_json(path, default=[])

    def save_users(self, users: list[dict[str, Any]]) -> None:
        path = self._settings.path_for("USERS_FILE")
        self.write_json(path, users)

    def load_portfolios(self) -> list[dict[str, Any]]:
        path = self._settings.path_for("PORTFOLIOS_FILE")
        return self.read_json(path, default=[])

    def save_portfolios(self, portfolios: list[dict[str, Any]]) -> None:
        path = self._settings.path_for("PORTFOLIOS_FILE")
        self.write_json(path, portfolios)

    def load_rates(self) -> dict[str, Any]:
        path = self._settings.path_for("RATES_FILE")
        return self.read_json(path, default={"pairs": {}, "last_refresh": None})

    def save_rates(self, rates: dict[str, Any]) -> None:
        path = self._settings.path_for("RATES_FILE")
        self.write_json(path, rates)

    def load_history(self) -> list[dict[str, Any]]:
        path = self._settings.path_for("HISTORY_FILE")
        return self.read_json(path, default=[])

    def save_history(self, history: list[dict[str, Any]]) -> None:
        path = self._settings.path_for("HISTORY_FILE")
        self.write_json(path, history)