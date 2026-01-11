from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.core.utils import utcnow_iso
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict[str, dict]:
        raise NotImplementedError

#Класс для работы с криптовалютным API
class CoinGeckoClient(BaseApiClient):
    def __init__(self) -> None:
        self._cfg = ParserConfig()

    def fetch_rates(self) -> dict[str, dict]:
        url = f"{self._cfg.COINGECKO_ROOT}/simple/price"
        ids = [self._cfg.CRYPTO_ID_MAP[c] for c in self._cfg.CRYPTO_CURRENCIES]
        params = {
            "ids": ",".join(ids),
            "vs_currencies": self._cfg.BASE_CURRENCY.lower(),
        }

        headers = {}
        headers["x-cg-demo-api-key"] = self._cfg.COINGECKO_API_KEY

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=self._cfg.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                raise ApiRequestError(reason=f"CoinGecko код статуса ={resp.status_code} body={resp.text[:200]}")
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(reason=f"CoinGecko: возникла проблема на стороне сервиса {e}")

        out: dict[str, dict] = {}
        ts = utcnow_iso()
        for code, raw_id in self._cfg.CRYPTO_ID_MAP.items():
            node = data.get(raw_id, {})
            price = node.get(self._cfg.BASE_CURRENCY.lower())
            if isinstance(price, (int, float)):
                pair = f"{code}_{self._cfg.BASE_CURRENCY}"
                out[pair] = {"rate": float(price), "updated_at": ts, "source": "CoinGecko"}
        return out

#Класс для работы с апи-ключом фиатной валюты
class ExchangeRateApiClient(BaseApiClient):
    def __init__(self) -> None:
        self._cfg = ParserConfig()

    def fetch_rates(self) -> dict[str, dict]:
        if not self._cfg.EXCHANGERATE_API_KEY:
            raise ApiRequestError(reason="Не задан апи-ключ для фиатных валют")

        url = f"{self._cfg.EXCHANGERATE_API_URL}/{self._cfg.EXCHANGERATE_API_KEY}/latest/{self._cfg.BASE_CURRENCY}"
        try:
            resp = requests.get(url, timeout=self._cfg.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                raise ApiRequestError(reason=f"ExchangeRate-API код статуса={resp.status_code}")
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(reason=f"ExchangeRate-API: возникла проблема на стороне сервиса {e}")

        conversion_rates = data.get("conversion_rates", {})
        ts = utcnow_iso()

        out: dict[str, dict] = {}
        for code in self._cfg.FIAT_CURRENCIES:
            value = conversion_rates.get(code)
            if isinstance(value, (int, float)) and float(value) != 0:
                pair = f"{code}_{self._cfg.BASE_CURRENCY}"
                out[pair] = {"rate": 1.0 / float(value), "updated_at": ts, "source": "ExchangeRate-API"}
        return out