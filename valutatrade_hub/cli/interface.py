#Импорты
from __future__ import annotations

import shlex

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import CoreUseCases

#Парсер аргументов
def _parse_kwargs(tokens: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--"):
            key = t[2:]
            if i + 1 >= len(tokens):
                out[key] = ""
                i += 1
            else:
                out[key] = tokens[i + 1]
                i += 2
        else:
            i += 1
    return out

#Реализация интерфейса
def main() -> None:
    uc = CoreUseCases()

    print("\nПривет, это ValutaTrade Hub, где обмен валют живет в консоли") #пример комманд и формат ввода
    print("\nСписок команд")
    print("\n> register --username <тут_имя> --password <не меньше 4 циферок>")
    print("\n> login --username <тут_имя> --password <как при регистрации>")
    print("\n> show-portfolio [--base <код валюты>]")
    print("\n> buy --currency <код валюты> --amount <количество>")
    print("\n> sell --currency <код валюты> --amount <количество>")
    print("\n> get-rate --from <код валюты> --to <код валюты>")
    print("\n> update-rates [--source coingecko|exchangerate]")
    print("\n> show-rates [--currency <код валюты>] [--top 2]")
    print("\nДля выхода: exit, quit")

    while True: #обработка команд
        try:
            raw = input("> ").strip()
            if not raw:
                continue
            if raw.lower() in {"exit", "quit"}:
                print("До свидания!")
                return
            if raw.lower() in {"exit", "quit"}:
                uc.shutdown()
                return

            tokens = shlex.split(raw)
            cmd = tokens[0]
            args = tokens[1:]
            kw = _parse_kwargs(args)

            try:
                if cmd == "register":
                    print(
                        uc.register(
                            username=kw.get("username", ""),
                            password=kw.get("password", ""),
                        )
                    )

                elif cmd == "login":
                    print(
                        uc.login(
                            username=kw.get("username", ""),
                            password=kw.get("password", ""),
                        )
                    )

                elif cmd == "show-portfolio":
                    base = kw.get("base", "USD")
                    print(uc.show_portfolio(base=base))

                elif cmd == "buy":
                    currency = kw.get("currency", "")
                    amount = float(kw.get("amount", "0"))
                    print(uc.buy(currency_code=currency, amount=amount))

                elif cmd == "sell":
                    currency = kw.get("currency", "")
                    amount = float(kw.get("amount", "0"))
                    print(uc.sell(currency_code=currency, amount=amount))

                elif cmd == "get-rate":
                    from_code = kw.get("from", "")
                    to_code = kw.get("to", "")
                    print(uc.get_rate(from_code=from_code, to_code=to_code))

                elif cmd == "update-rates":
                    source = kw.get("source", "all")
                    print(uc.update_rates(source=source))

                elif cmd == "show-rates":
                    currency = kw.get("currency")
                    top_raw = kw.get("top")
                    top = int(top_raw) if top_raw else None
                    print(uc.show_rates(currency=currency, top=top))

                else:
                    print("Неизвестная команда")
            except InsufficientFundsError as e:
                print(str(e))
            except CurrencyNotFoundError as e:
                print(str(e))
                print("Подсказка: используйте поддерживаемые коды (USD, EUR, BTC, ETH, SOL, RUB, GBP).")
            except ApiRequestError as e:
                print(str(e))
                print("Подсказка: попробуйте позже или выполните update-rates.")
            except PermissionError as e:
                print(str(e))
            except ValueError as e:
                print(str(e))

        except (EOFError, KeyboardInterrupt):
            uc.shutdown()
            return