from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from prettytable import PrettyTable #выводит таблицу в определеоном формате

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import parse_iso_dt, validate_amount
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.scheduler import RatesScheduler

#Реализация бизнес-логики
@dataclass
class Session:
    user_id: int | None = None
    username: str | None = None

#Основной класс для реализации логики
class CoreUseCases:
    def __init__(self) -> None:
        setup_logging()
        self._db = DatabaseManager()
        self._settings = SettingsLoader()
        self.session = Session()
        self._scheduler = RatesScheduler(interval_seconds=3600) #автообнолвение раз в час
        self._scheduler.start()

    def _ensure_logged_in(self) -> None:
        if self.session.user_id is None:
            raise PermissionError("Сначала выполните login") #проверка входа

    def _next_user_id(self, users: list[dict]) -> int:
        if not users:
            return 1
        return max(int(u["user_id"]) for u in users) + 1

    def _find_user_by_username(self, username: str) -> dict | None:
        users = self._db.load_users()
        for u in users:
            if u.get("username") == username:
                return u
        return None

    @log_action("REGISTER")
    def register(self, username: str, password: str) -> str:
        username = str(username).strip()
        password = str(password)

        if not username:
            raise ValueError("Имя не может быть пустым.") #проверка для регистрации
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        users = self._db.load_users()
        if any(u.get("username") == username for u in users):
            return f"Имя пользователя '{username}' уже занято"

        user_id = self._next_user_id(users)

        tmp_user = User(
            user_id=user_id,
            username=username,
            hashed_password="",
            salt=User.generate_salt(),
            registration_date=datetime.now(timezone.utc).replace(microsecond=0),
        )
        tmp_user.change_password(password)

        users.append(
            {
                "user_id": user_id,
                "username": tmp_user.username,
                "hashed_password": tmp_user.hashed_password,
                "salt": tmp_user.salt,
                "registration_date": tmp_user.registration_date.isoformat(),
            }
        )
        self._db.save_users(users) #сохранение пользователей в базу

        portfolios = self._db.load_portfolios()
        portfolios.append({"user_id": user_id, "wallets": {}})
        self._db.save_portfolios(portfolios)

        return (
            f"Пользователь '{username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username {username} --password ****"
        )

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> str:
        username = str(username).strip()
        password = str(password)

        user_row = self._find_user_by_username(username)
        if user_row is None:
            return f"Пользователь '{username}' не найден"

        user = User(
            user_id=int(user_row["user_id"]),
            username=str(user_row["username"]),
            hashed_password=str(user_row["hashed_password"]),
            salt=str(user_row["salt"]),
            registration_date=parse_iso_dt(str(user_row["registration_date"])) or datetime.now(),
        )

        if not user.verify_password(password):
            return "Неверный пароль"

        self.session.user_id = user.user_id
        self.session.username = user.username
        return f"Вы вошли как '{user.username}'"

    def _load_portfolio_for_session(self) -> Portfolio:
        self._ensure_logged_in()
        portfolios = self._db.load_portfolios()
        row = next((p for p in portfolios if int(p.get("user_id")) == self.session.user_id), None)
        if row is None:
            return Portfolio(user_id=int(self.session.user_id), wallets={})

        wallets_data = row.get("wallets", {}) or {}
        wallets: dict[str, Wallet] = {}
        for code, w in wallets_data.items():
            if isinstance(w, dict):
                balance = float(w.get("balance", 0.0))
                ccode = str(w.get("currency_code", code)).upper()
            else:
                balance = float(w)
                ccode = str(code).upper()
            wallets[ccode] = Wallet(currency_code=ccode, balance=balance)
        return Portfolio(user_id=int(self.session.user_id), wallets=wallets)

    def _save_portfolio(self, portfolio: Portfolio) -> None:
        portfolios = self._db.load_portfolios()
        row = next((p for p in portfolios if int(p.get("user_id")) == portfolio.user_id), None)
        wallets_dump = {c: {"currency_code": c, "balance": w.balance} for c, w in portfolio.wallets.items()}
        if row is None:
            portfolios.append({"user_id": portfolio.user_id, "wallets": wallets_dump})
        else:
            row["wallets"] = wallets_dump
        self._db.save_portfolios(portfolios)

    def _get_rate_pair(self, pair: str) -> tuple[float, str, str] | None:
        rates = self._db.load_rates()
        pairs = rates.get("pairs", {}) or {}
        obj = pairs.get(pair)
        if not isinstance(obj, dict):
            return None
        rate = obj.get("rate")
        updated_at = obj.get("updated_at")
        source = obj.get("source", "unknown")
        if not isinstance(rate, (int, float)) or not isinstance(updated_at, str):
            return None
        return float(rate), updated_at, str(source)

    def _get_rate(self, from_code: str, to_code: str) -> tuple[float, str, str] | None:
        direct = self._get_rate_pair(f"{from_code}_{to_code}")
        if direct is not None:
            return direct
        rev = self._get_rate_pair(f"{to_code}_{from_code}")
        if rev is None:
            return None
        rate, updated_at, source = rev
        if rate == 0:
            return None
        return 1.0 / rate, updated_at, source

    def _is_rate_fresh(self, updated_at: str) -> bool:
        ttl = int(self._settings.get("RATES_TTL_SECONDS", 300))
        dt = parse_iso_dt(updated_at)
        if dt is None:
            return False
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).total_seconds() <= ttl

    @log_action("GET_RATE")
    def get_rate(self, from_code: str, to_code: str) -> str:
        from_code = get_currency(from_code).code
        to_code = get_currency(to_code).code

        cached = self._get_rate(from_code, to_code)
        if cached is not None:
            rate, updated_at, _source = cached
            if self._is_rate_fresh(updated_at):
                inv = 1 / rate if rate != 0 else 0.0
                return (
                    f"Курс {from_code}→{to_code}: {rate:.8f} (обновлено: {updated_at})\n" #получение курсов
                    f"Обратный курс {to_code}→{from_code}: {inv:.8f}"
                )

        self.update_rates(source="all")

        cached2 = self._get_rate(from_code, to_code)
        if cached2 is None:
            raise ApiRequestError(reason=f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже.")

        rate2, updated_at2, _source2 = cached2
        inv2 = 1 / rate2 if rate2 != 0 else 0.0
        return (
            f"Курс {from_code}→{to_code}: {rate2:.8f} (обновлено: {updated_at2})\n"
            f"Обратный курс {to_code}→{from_code}: {inv2:.8f}"
        )

    @log_action("BUY", verbose=True)
    def buy(self, currency_code: str, amount: float) -> str:
        self._ensure_logged_in()
        currency_code = get_currency(currency_code).code
        amount = validate_amount(amount)

        portfolio = self._load_portfolio_for_session()

        wallet = portfolio.get_wallet(currency_code)
        if wallet is None:
            wallet = portfolio.add_currency(currency_code)

        old_balance = wallet.balance

        if currency_code == "USD":
            wallet.deposit(amount)
            self._save_portfolio(portfolio)
            return (
                f"Покупка выполнена: {amount:.4f} USD\n"
                f"Изменения в портфеле:\n- USD: было {old_balance:.4f} → стало {wallet.balance:.4f}" #реализация покупки
            )

        usd = portfolio.get_wallet("USD")
        if usd is None:
            usd = portfolio.add_currency("USD")

        rate_data = self._get_rate(currency_code, "USD")
        if rate_data is None:
            raise ApiRequestError(reason=f"Не удалось получить курс для {currency_code}→USD")
        rate, _updated_at, _source = rate_data

        cost = amount * rate
        usd.withdraw(cost)
        wallet.deposit(amount)
        self._save_portfolio(portfolio)

        return (
            f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"Оценочная стоимость покупки: {cost:,.2f} USD"
        )

    @log_action("SELL", verbose=True)
    def sell(self, currency_code: str, amount: float) -> str:
        self._ensure_logged_in()
        currency_code = get_currency(currency_code).code
        amount = validate_amount(amount)

        portfolio = self._load_portfolio_for_session()
        wallet = portfolio.get_wallet(currency_code)
        if wallet is None:
            return (
                f"У вас нет кошелька '{currency_code}'. Добавьте валюту: она создаётся " #реализация функции продажи
                f"автоматически при первой покупке."
            )

        old_balance = wallet.balance

        if currency_code == "USD":
            wallet.withdraw(amount)
            self._save_portfolio(portfolio)
            return (
                f"Продажа выполнена: {amount:.2f} USD\n"
                f"Изменения в портфеле:\n- USD: было {old_balance:.2f} → стало {wallet.balance:.2f}"
            )

        usd = portfolio.get_wallet("USD")
        if usd is None:
            usd = portfolio.add_currency("USD")

        rate_data = self._get_rate(currency_code, "USD")
        if rate_data is None:
            raise ApiRequestError(reason=f"Не удалось получить курс для {currency_code}→USD")
        rate, _updated_at, _source = rate_data

        wallet.withdraw(amount)
        proceeds = amount * rate
        usd.deposit(proceeds)
        self._save_portfolio(portfolio)

        return (
            f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"Оценочная выручка: {proceeds:,.2f} USD"
        )

    def show_portfolio(self, base: str = "USD") -> str:
        self._ensure_logged_in()
        base = get_currency(base).code
        portfolio = self._load_portfolio_for_session()

        if not portfolio.wallets:
            return "Кошельков нет. Купите валюту: buy --currency USD --amount 100"

        lines: list[str] = []
        lines.append(f"Портфель пользователя '{self.session.username}' (база: {base}):")

        total = 0.0
        for code, wallet in sorted(portfolio.wallets.items()):
            if code == base:
                value = wallet.balance
                lines.append(f"- {code}: {wallet.balance:.4f}  → {value:,.2f} {base}")
                total += value
                continue

            rate_data = self._get_rate(code, base)
            if rate_data is None:
                lines.append(f"- {code}: {wallet.balance:.4f}  → (нет курса к {base})")
                continue

            rate, _updated_at, _source = rate_data
            value = wallet.balance * rate
            lines.append(f"- {code}: {wallet.balance:.4f}  → {value:,.2f} {base}")
            total += value

        lines.append("--------------------------")
        lines.append(f"ИТОГО: {total:,.2f} {base}")
        return "\n".join(lines)

    @log_action("UPDATE_RATES") #обновление курсов через внешние API
    def update_rates(self, source: str = "all") -> str:
        from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
        from valutatrade_hub.parser_service.storage import RatesStorage
        from valutatrade_hub.parser_service.updater import RatesUpdater

        clients = []
        src = str(source).strip().lower()
        if src in {"all", ""}:
            clients = [CoinGeckoClient(), ExchangeRateApiClient()]
        elif src == "coingecko":
            clients = [CoinGeckoClient()]
        elif src == "exchangerate":
            clients = [ExchangeRateApiClient()]
        else:
            raise ValueError("source должен быть: coingecko, exchangerate или all")

        updater = RatesUpdater(clients=clients, storage=RatesStorage())
        result = updater.run_update()
        return (
            "Update successful. "
            f"Total rates updated: {result['total']}. Last refresh: {result['last_refresh']}"
        )

    def show_rates(self, currency: str | None = None, top: int | None = None) -> str:
        rates = self._db.load_rates()
        pairs = rates.get("pairs", {}) or {}
        last_refresh = rates.get("last_refresh")

        if not pairs:
            return "Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные."

        items = []
        for pair, obj in pairs.items():
            if not isinstance(obj, dict):
                continue
            rate = obj.get("rate")
            updated_at = obj.get("updated_at")
            if not isinstance(rate, (int, float)):
                continue
            if currency:
                c = get_currency(currency).code
                if not (pair.startswith(f"{c}_") or pair.endswith(f"_{c}")):
                    continue
            items.append((pair, float(rate), str(updated_at) if updated_at else ""))

        if top is not None:
            items.sort(key=lambda x: x[1], reverse=True)
            items = items[: int(top)]
        else:
            items.sort(key=lambda x: x[0])

        table = PrettyTable()
        table.field_names = ["PAIR", "RATE", "UPDATED_AT"]
        for pair, rate, updated_at in items:
            table.add_row([pair, f"{rate:.8f}", updated_at])

        header = f"Rates from cache (updated at {last_refresh}):"
        return header + "\n" + str(table)

    def shutdown(self) -> None:
        self._scheduler.stop()