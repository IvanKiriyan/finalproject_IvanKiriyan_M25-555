from __future__ import annotations

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError

#Реализация базового класса Currency
class Currency(ABC):
    name: str
    code: str

    def __init__(self, name: str, code: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("введите имя")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("ввдите код")
        code = code.strip().upper()
        if not (2 <= len(code) <= 5) or " " in code:
            raise ValueError("введите код, пример: USD, RUB")

        self.name = name.strip()
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        raise NotImplementedError

#Класс фиатных валют - традиционных
class FiatCurrency(Currency):
    issuing_country: str

    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name=name, code=code)
        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("не оставляйте строчку пустой")
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

#Класс криптовалют
class CryptoCurrency(Currency):
    algorithm: str
    market_cap: float

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float) -> None:
        super().__init__(name=name, code=code)
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("не оставляйте строку пустой")
        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("число не меньше или равно нулю")
        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )

#Реестр валют
_CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("Pound Sterling", "GBP", "United Kingdom"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.50e11),
    "SOL": CryptoCurrency("Solana", "SOL", "PoH", 8.00e10),
}

#Фабричный метод get_currency
def get_currency(code: str) -> Currency:
    if not isinstance(code, str) or not code.strip():
        raise CurrencyNotFoundError(code=str(code))
    code = code.strip().upper()
    currency = _CURRENCY_REGISTRY.get(code)
    if currency is None:
        raise CurrencyNotFoundError(code=code)
    return currency