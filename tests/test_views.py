import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import main_views


@patch("src.views.get_greeting")
@patch("src.views.load_data_from_file")
@patch("src.views.filter_data_by_month_range")
@patch("src.views.get_card_statistics")
@patch("src.views.get_top_transactions")
@patch("src.views.get_market_data")
def test_main_views_success(
        mock_market, mock_top, mock_cards, mock_filter, mock_load, mock_greeting, mock_utils_data
):
    """Тест успешной сборки JSON-ответа"""
    mock_greeting.return_value = mock_utils_data["greeting"]
    mock_load.return_value = pd.DataFrame({"test": [1]})
    mock_filter.return_value = pd.DataFrame({"test": [1]})
    mock_cards.return_value = mock_utils_data["cards"]
    mock_top.return_value = mock_utils_data["top"]
    mock_market.return_value = mock_utils_data["market"]

    result_json = main_views("2023-01-01 12:00:00")
    result = json.loads(result_json)

    assert result["greeting"] == "Добрый день"
    assert result["cards"] == mock_utils_data["cards"]
    assert result["currency_rates"][0]["currency"] == "USD"
    assert result["stock_prices"][0]["stock"] == "AAPL"

    mock_load.assert_called_once()
    mock_market.assert_called_once()


@patch("src.views.load_data_from_file")
def test_main_views_file_not_found(mock_load):
    """Тест обработки ситуации, когда файл не загрузился"""
    mock_load.return_value = None

    result_json = main_views("2023-01-01 12:00:00")
    result = json.loads(result_json)

    assert "error" in result
    assert result["error"] == "File not found or empty"


@pytest.mark.parametrize("market_return", [
    ({"currencies": [], "stocks": []}),
    ({}),
])
@patch("src.views.get_greeting")
@patch("src.views.load_data_from_file")
@patch("src.views.filter_data_by_month_range")
@patch("src.views.get_market_data")
def test_main_views_empty_market_data(
        mock_market, mock_filter, mock_load, mock_greeting, market_return
):
    """Тест устойчивости к отсутствию данных о валютах/акциях"""
    mock_greeting.return_value = "Привет"
    mock_load.return_value = pd.DataFrame({"test": [1]})
    mock_market.return_value = market_return

    with patch("src.views.get_card_statistics", return_value=[]), \
            patch("src.views.get_top_transactions", return_value=[]):
        result_json = main_views("2023-01-01 12:00:00")
        result = json.loads(result_json)

        assert result["currency_rates"] == []
        assert result["stock_prices"] == []