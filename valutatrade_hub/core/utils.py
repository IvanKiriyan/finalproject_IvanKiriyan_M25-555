from __future__ import annotations

from datetime import datetime, timezone

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError

#Проверка валютного кода через реестр валют
def validate_currency_code(code: str) -> str:
    try:
        currency = get_currency(code)
    except CurrencyNotFoundError:
        raise
    return currency.code


def validate_amount(amount) -> float:
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть положительным числом")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return amount


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_dt(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    v = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None