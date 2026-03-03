import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Hashable, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")


def get_greeting(date_str: str) -> str:
    """
    Функция отвечает за вывод приветствия в зависимости от времени суток
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour

    if 5 <= hour < 12:
        message = "Доброе утро"
    elif 12 <= hour < 18:
        message = "Добрый день"
    elif 18 <= hour < 23:
        message = "Добрый вечер"
    else:
        message = "Доброй ночи"

    return f'"{message}"'


def load_data_from_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Функция считывает данные (Excel) для последующей передачи их в основную функцию
    """
    try:
        return pd.read_excel(file_path)
    except Exception:
        return None


def filter_data_by_month_range(df: pd.DataFrame, date_str: str, date_column: str = "Дата операции") -> pd.DataFrame:
    """
    Фильтрует данные с начала месяца входящей даты по саму дату.
    """
    end_date = pd.to_datetime(date_str)
    start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

    df[date_column] = pd.to_datetime(df[date_column], dayfirst=True)

    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df.loc[mask].sort_values(by=date_column, ascending=False)


def get_card_statistics(df: pd.DataFrame) -> list[dict[Hashable, Any]]:
    """ "
    Функция по каждой карте выдает последние 4 цифры, общую сумма расходов, кешбэк
    """
    df_card_numbers = df.dropna(subset=["Номер карты"]).copy()
    df_card_numbers["last_digits"] = df_card_numbers["Номер карты"].astype(str).str.slice(-4)

    stats = df_card_numbers.groupby("last_digits")["Сумма операции"].sum().reset_index()
    stats.columns = ["last_digits", "total_spent"]

    stats["total_spent"] = stats["total_spent"].abs().round(2)
    stats["cashback"] = (stats["total_spent"] / 100).round(2)

    return stats.to_dict(orient="records")


def get_top_transactions(df: pd.DataFrame) -> list[Any]:
    """
    Функция выдает топ-5 транзакций по сумме платежа
    """
    df_copy = df.copy()
    df_copy["abs_amount"] = df_copy["Сумма операции"].abs()

    top_5 = df_copy.sort_values(by="abs_amount", ascending=False).head(5)

    result = top_5.rename(
        columns={
            "Дата операции": "date",
            "Сумма операции": "amount",
            "Категория": "category",
            "Описание": "description",
        }
    )

    result = result.sort_values(by="date", ascending=False)

    result["date"] = result["date"].dt.strftime("%d.%m.%Y")

    result["amount"] = result["amount"].abs()

    return result[["date", "amount", "category", "description"]].to_dict(orient="records")


def get_market_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    Функция выдает данные о валютах и ценах на акции
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    settings_path = project_root / "user_settings.json"

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError, json.JSONDecodeError:
        return {"currencies": [], "stocks": []}

    user_currencies = settings.get("user_currencies", [])
    user_stocks = settings.get("user_stocks", [])

    currencies_result = []

    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        if response.status_code == 200:
            valutes = response.json().get("Valute", {})
            for code in user_currencies:
                if code in valutes:
                    currencies_result.append({"currency": code, "rate": round(valutes[code]["Value"], 2)})
    except requests.exceptions.RequestException:
        pass

    stocks_result = []
    if user_stocks and API_KEY:
        for symbol in user_stocks:
            symbol = symbol.strip().upper()

            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"

            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    current_price = data.get("c", 0)

                    if current_price > 0:
                        stocks_result.append({"stock": symbol, "price": round(current_price, 2)})
            except Exception:
                pass

    return {"currencies": currencies_result, "stocks": stocks_result}
