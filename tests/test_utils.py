import json
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
import requests

from src.utils import (
    filter_data_by_month_range,
    get_card_statistics,
    get_greeting,
    get_market_data,
    get_top_transactions,
    load_data_from_file,
)


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("2023-10-15 09:00:00", '"Доброе утро"'),
        ("2023-10-15 15:00:00", '"Добрый день"'),
        ("2023-10-15 20:00:00", '"Добрый вечер"'),
        ("2023-10-15 01:00:00", '"Доброй ночи"'),
    ],
)
def test_get_greeting(date_str: str, expected: str) -> None:
    assert get_greeting(date_str) == expected


def test_filter_data_by_month_range_sorting() -> None:
    data = {"Дата операции": ["01.10.2023", "15.10.2023"], "Сумма": [100, 200]}
    df = pd.DataFrame(data)
    result = filter_data_by_month_range(df, "2023-10-20")
    assert result.iloc[0]["Дата операции"] == pd.to_datetime("2023-10-15")


def test_get_card_statistics() -> None:
    data = {"Номер карты": ["*1111", "*1111", "*2222", None], "Сумма операции": [-100.0, -50.0, -200.0, -10.0]}
    df = pd.DataFrame(data)
    result = get_card_statistics(df)

    card_1111 = next(item for item in result if item["last_digits"] == "1111")
    assert card_1111["total_spent"] == 150.0
    assert card_1111["cashback"] == 1.5
    assert len(result) == 2


@patch("requests.get")
def test_get_market_data(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Valute": {"USD": {"Value": 75.5}}}
    mock_get.return_value = mock_response

    from src.utils import get_market_data

    with patch("json.load", return_value={"user_currencies": ["USD"], "user_stocks": []}):
        with patch("builtins.open", MagicMock()):
            result = get_market_data()
            assert result["currencies"][0]["currency"] == "USD"
            assert result["currencies"][0]["rate"] == 75.5


@patch("src.utils.requests.get")
def test_get_market_data_empty_settings(mock_get: MagicMock) -> None:
    """Тест когда файл настроек пуст или отсутствует"""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = get_market_data()
        assert result == {"currencies": [], "stocks": []}


@patch("src.utils.requests.get")
def test_get_market_data_stocks_success(mock_get: MagicMock, mock_settings: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"c": 150.0}
    mock_get.return_value = mock_response

    with (
        patch("src.utils.API_KEY", "test_key"),
        patch("json.load", return_value={"user_currencies": [], "user_stocks": ["AAPL"]}),
    ):
        with patch("builtins.open", mock_open()):
            result = get_market_data()
            assert result["stocks"][0]["stock"] == "AAPL"
            assert result["stocks"][0]["price"] == 150.0


@patch("pandas.read_excel")
def test_load_data_from_file_fail(mock_read: MagicMock) -> None:
    mock_read.side_effect = Exception("Read error")
    assert load_data_from_file("path.xlsx") is None


@patch("builtins.open", side_effect=FileNotFoundError)
def test_get_market_data_no_settings(mock_open_err: MagicMock) -> None:
    result = get_market_data()
    assert result == {"currencies": [], "stocks": []}


@patch("builtins.open", new_callable=mock_open, read_data='{ "invalid": json }')
def test_get_market_data_bad_json(mock_file: MagicMock) -> None:
    with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
        from src.utils import get_market_data

        result = get_market_data()
        assert result == {"currencies": [], "stocks": []}


@patch("src.utils.requests.get")
def test_get_market_data_api_fail(mock_get: MagicMock) -> None:
    mock_get.side_effect = requests.exceptions.RequestException
    result = get_market_data()
    assert result["currencies"] == []


@patch("pandas.read_excel", side_effect=Exception("Error"))
def test_load_data_logging(mock_read: MagicMock) -> None:
    assert load_data_from_file("any.xlsx") is None


def test_filter_sorting() -> None:
    df = pd.DataFrame({"Дата операции": ["01.01.2023", "10.01.2023"], "Сумма": [1, 2]})
    result = filter_data_by_month_range(df, "2023-01-15")
    assert result.iloc[0]["Дата операции"] == pd.to_datetime("2023-01-10")


def test_get_top_transactions_logic(mock_utils_data_with_minus: MagicMock) -> None:
    df = pd.DataFrame(mock_utils_data_with_minus)
    result = get_top_transactions(df)
    assert len(result) == 5
    amounts = [item["amount"] for item in result]
    assert 5000.0 in amounts
    assert isinstance(result[0]["date"], str)
    assert "." in result[0]["date"]
    assert result[0]["date"] == "10.10.2023"


@patch("src.utils.pd.read_excel")
def test_load_data_from_file_success(mock_read: MagicMock) -> None:
    """Тест успешного чтения файла"""
    mock_df = pd.DataFrame({"column1": [1, 2], "column2": [3, 4]})
    mock_read.return_value = mock_df

    result = load_data_from_file("test.xlsx")

    assert result is not None
    assert len(result) == 2
    assert isinstance(result, pd.DataFrame)

    mock_read.assert_called_once_with("test.xlsx")


def test_get_card_statistics_empty_data() -> None:
    """Тест для случая, когда данных о картах нет"""
    df_empty = pd.DataFrame(columns=["Номер карты", "Сумма операции"])

    df_nan = pd.DataFrame({"Номер карты": [None, None], "Сумма операции": [100, 200]})

    assert get_card_statistics(df_empty) == []
    assert get_card_statistics(df_nan) == []
