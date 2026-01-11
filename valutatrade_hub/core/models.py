from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Any

"""Реализация класса пользователя"""
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
            raise ValueError("Имя не может быть пустым.") #проверка юзернейма
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
            raise ValueError("Пароль должен быть не короче 4 символов") #проверка пароля
        new_salt = self.generate_salt()
        new_hash = self._hash_password(new_password, new_salt)
        self._salt = new_salt
        self._hashed_password = new_hash

    def verify_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        return self._hash_password(password, self._salt) == self._hashed_password