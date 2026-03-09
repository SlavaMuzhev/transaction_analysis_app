import json
from pathlib import Path

from src.utils import (filter_data_by_month_range, get_card_statistics, get_greeting, get_market_data,
                       get_top_transactions, load_data_from_file)


def main_views(date_str: str) -> str:
    """
    Главная функция, которая собирает все данные в единый JSON-ответ
    """
    # Вывод приветствия
    greeting = get_greeting(date_str)

    # Загрузка данных
    src_path = Path(__file__).resolve().parent
    file_path = src_path.parent / "data" / "operations.xlsx"

    data = load_data_from_file(str(file_path))

    if data is None:
        return json.dumps({"error": "File not found or empty"}, ensure_ascii=False)

    # Определяем диапазон дат с начала месяца по входящую дату
    filtered_data = filter_data_by_month_range(data, date_str)

    # По каждой карте получаем последние 4 цифры, общая сумма расходов, кешбэк
    card_statistics = get_card_statistics(filtered_data)

    # Получаем топ-5 транзакций по сумме платежа
    top_transactions = get_top_transactions(filtered_data)

    # Получаем данные о валютах и ценах на акции
    market_data = get_market_data()

    # Сборка финального словаря
    response = {
        "greeting": greeting.replace('"', ""),
        "cards": card_statistics,
        "top_transactions": top_transactions,
        "currency_rates": market_data.get("currencies", []),
        "stock_prices": market_data.get("stocks", []),
    }

    # Возвращаем JSON-строку с поддержкой кириллицы
    return json.dumps(response, ensure_ascii=False, indent=2)
