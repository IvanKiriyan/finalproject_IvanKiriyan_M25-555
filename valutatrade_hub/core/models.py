from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Any

from valutatrade_hub.core.exceptions import InsufficientFundsError

#Реализация класса длдя пользователей
class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self._user_id = int(user_id)
        self.username = username
        self._hashed_password = str(hashed_password)
        self._salt = str(salt)
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя не может быть пустым.") #проверка имени
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def get_user_info(self) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        raw = (password + salt).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def generate_salt() -> str:
        return secrets.token_hex(8)

    def change_password(self, new_password: str) -> None:
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов") #проверка паролья
        new_salt = self.generate_salt()
        new_hash = self._hash_password(new_password, new_salt)
        self._salt = new_salt
        self._hashed_password = new_hash

    def verify_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        return self._hash_password(password, self._salt) == self._hashed_password

#Класс для кошелька
class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        self.currency_code = str(currency_code).strip().upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("баланс должен быть числом")
        value = float(value)
        if value < 0:
            raise ValueError("баланс не должен быть ниже нуля")
        self._balance = value

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValueError("'amount' должен быть положительным")
        self.balance = self.balance + float(amount)

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValueError("'amount' должен быть положительным")
        amount = float(amount)
        if amount > self.balance:
            raise InsufficientFundsError(
                available=self.balance,
                required=amount,
                code=self.currency_code,
            )
        self.balance = self.balance - amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self.balance:.4f}"

#Класс для портфеля
class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None) -> None:
        self._user_id = int(user_id)
        self._wallets: dict[str, Wallet] = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self):
        return getattr(self, "_user", None)

    @property
    def wallets(self) -> dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        currency_code = str(currency_code).strip().upper()
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк '{currency_code}' уже существует") #проверка для кошельков
        wallet = Wallet(currency_code=currency_code, balance=0.0)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        currency_code = str(currency_code).strip().upper()
        return self._wallets.get(currency_code)

#Временные валюты до подключения к внешним ресурсам
    def get_total_value(self, base_currency: str = "USD") -> float:
        exchange_rates = {
            "USD_USD": 1.0,
            "EUR_USD": 1.07,
            "BTC_USD": 59300.0,
            "ETH_USD": 3720.0,
            "RUB_USD": 0.010,
        }
        base_currency = str(base_currency).strip().upper()
        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base_currency:
                total += wallet.balance
                continue
            pair = f"{code}_{base_currency}"
            rate = exchange_rates.get(pair)
            if rate is None:
                continue
            total += wallet.balance * float(rate)
        return total