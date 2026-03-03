import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pandas as pd
import pytest
import requests

from src.utils import (filter_data_by_month_range, get_card_statistics, get_greeting,
                       get_market_data, get_top_transactions, load_data_from_file)


@pytest.mark.parametrize("date_str, expected", [
    ("2023-01-01 09:00:00", '"Доброе утро"'),
    ("2023-01-01 13:00:00", '"Добрый день"'),
    ("2023-01-01 19:00:00", '"Добрый вечер"'),
    ("2023-01-01 02:00:00", '"Доброй ночи"'),
])
def test_get_greeting(date_str, expected):
    assert get_greeting(date_str) == expected


@patch("pandas.read_excel")
def test_load_data_from_file_success(mock_read):
    mock_read.return_value = pd.DataFrame({"test": [1]})
    result = load_data_from_file("path/to/file.xlsx")
    assert isinstance(result, pd.DataFrame)


@patch("pandas.read_excel")
def test_load_data_from_file_error(mock_read):
    mock_read.side_effect = Exception("Error")
    assert load_data_from_file("invalid_path") is None


def test_get_top_transactions(sample_df):
    result = get_top_transactions(sample_df)
    # После сортировки по сумме (abs) 2000.0 должна быть первой
    assert len(result) == 3
    assert result[0]["amount"] == 2000.0
    assert result[0]["description"] == "Пятерочка"


@patch("src.utils.requests.get")
@patch("builtins.open", new_callable=mock_open, read_data='{}')
@patch("json.load")
def test_get_market_data(mock_json, mock_file, mock_get, mock_settings):
    mock_json.return_value = mock_settings

    mock_response_cbr = MagicMock()
    mock_response_cbr.status_code = 200
    mock_response_cbr.json.return_value = {"Valute": {"USD": {"Value": 75.5}}}

    mock_response_stock = MagicMock()
    mock_response_stock.status_code = 200
    mock_response_stock.json.return_value = {"c": 150.0}

    mock_get.side_effect = [mock_response_cbr, mock_response_stock, mock_response_stock]

    with patch("pathlib.Path.resolve", return_value=Path("/test/utils.py")), \
            patch("src.utils.API_KEY", "test_key"):
        result = get_market_data()

    assert result["currencies"][0]["currency"] == "USD"
    assert result["currencies"][0]["rate"] == 75.5
    assert result["stocks"][0]["stock"] == "AAPL"


@patch("src.utils.requests.get")
@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
def test_get_market_data_api_error(mock_json, mock_file, mock_get):
    """Тест поведения при ошибке API"""
    mock_json.return_value = {"user_currencies": ["USD"]}
    mock_get.side_effect = requests.exceptions.RequestException

    with patch("pathlib.Path.resolve", return_value=Path("/test/utils.py")):
        result = get_market_data()

    assert result["currencies"] == []


@pytest.mark.parametrize("filter_date, expected_count", [
    ("2023-01-16 00:00:00", 2),
    ("2023-01-31 23:59:59", 3),
    ("2023-02-01 00:00:00", 0),
])
def test_filter_data_by_month_range_parametrized(sample_df, filter_date, expected_count):
    """Тест фильтрации данных по диапазону дат (с начала месяца до указанной даты)"""
    result = filter_data_by_month_range(sample_df, filter_date)
    assert len(result) == expected_count
    if expected_count > 0:
        assert all(result["Дата операции"] <= pd.to_datetime(filter_date))


def test_get_card_statistics_logic(sample_df):
    """Тест расчета трат и кэшбэка по картам"""

    result = get_card_statistics(sample_df)

    assert len(result) == 2

    card_1111 = next(item for item in result if item["last_digits"] == "1111")
    card_2222 = next(item for item in result if item["last_digits"] == "2222")

    assert card_1111["total_spent"] == 3000.0
    assert card_1111["cashback"] == 30.0

    assert card_2222["total_spent"] == 500.0
    assert card_2222["cashback"] == 5.0


def test_get_card_statistics_empty():
    """Проверка поведения при пустом DataFrame или отсутствии номеров карт"""
    empty_df = pd.DataFrame(columns=["Номер карты", "Сумма операции"])
    result = get_card_statistics(empty_df)
    assert result == []
