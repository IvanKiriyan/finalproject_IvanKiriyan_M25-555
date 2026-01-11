from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    tomllib = None

#Реализация Singleton
class SettingsLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._cache = {}
            obj._loaded = False
            cls._instance = obj
        return cls._instance

    def _load(self) -> None:
        if self._loaded:
            return

        defaults = {
            "DATA_DIR": "data", #путь к файлам для записи данных
            "USERS_FILE": "users.json",
            "PORTFOLIOS_FILE": "portfolios.json",
            "RATES_FILE": "rates.json",
            "HISTORY_FILE": "exchange_rates.json",
            "RATES_TTL_SECONDS": 300,
            "DEFAULT_BASE_CURRENCY": "USD",
            "LOG_DIR": "logs",
        }

        data = dict(defaults)

        pyproject = Path("pyproject.toml")
        if tomllib is not None and pyproject.exists():
            raw = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            tool_cfg = raw.get("tool", {}).get("valutatrade", {})
            if isinstance(tool_cfg, dict):
                data.update(tool_cfg)

        self._cache = data
        self._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        self._load()
        return self._cache.get(key, default)

    def reload(self) -> None:
        self._loaded = False
        self._cache = {}
        self._load()

    def data_dir(self) -> Path:
        return Path(self.get("DATA_DIR", "data"))

    def path_for(self, filename_key: str) -> Path:
        return self.data_dir() / str(self.get(filename_key))