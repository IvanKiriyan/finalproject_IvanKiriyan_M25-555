from __future__ import annotations

import os
from dataclasses import dataclass

#Подключаем внешние ключи
@dataclass(frozen=True)
class ParserConfig:
    COINGECKO_API_KEY: str = os.getenv(
        "COINGECKO_DEMO_API_KEY",
        "CG-TXJWpkRhJ3Zp2arCLQsuucp4",
    )

    EXCHANGERATE_API_KEY: str = os.getenv(
        "EXCHANGERATE_API_KEY",
        "e37414520198fb083ae33b87",
    )

    COINGECKO_ROOT: str = "https://api.coingecko.com/api/v3"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL")

    REQUEST_TIMEOUT: int = 10

    CRYPTO_ID_MAP: dict[str, str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "CRYPTO_ID_MAP",
            {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            },
        )