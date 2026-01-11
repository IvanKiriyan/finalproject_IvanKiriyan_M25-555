#Реализация классов пользовательских исключений
#Если нед денег:
class InsufficientFundsError(Exception):
    def __init__(self, available: float, required: float, code: str) -> None:
        msg = (
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        super().__init__(msg)
        self.available = available
        self.required = required
        self.code = code

#Если не найдена валюьа
class CurrencyNotFoundError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code

#Если внешний апи сбился
class ApiRequestError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason