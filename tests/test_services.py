import json
from typing import Any, Dict

import pandas as pd

from src.services import analyze_cashback_categories


def test_analyze_cashback_success(sample_data: pd.DataFrame) -> None:
    """Тест успешного расчета кешбэка за конкретный месяц"""
    result_json: str = analyze_cashback_categories(sample_data, 2021, 12)
    result: Dict[str, Any] = json.loads(result_json)

    assert result["Супермаркеты"] == 100
    assert result["Аптеки"] == 50
    assert "01.01.2022" not in result_json


def test_analyze_cashback_empty_df() -> None:
    """Тест работы с пустым DataFrame"""
    empty_df: pd.DataFrame = pd.DataFrame()
    result: str = analyze_cashback_categories(empty_df, 2021, 12)
    assert result == "{}"


def test_analyze_cashback_no_bonus_column() -> None:
    """Тест ситуации, когда отсутствует колонка с бонусами"""
    bad_data: pd.DataFrame = pd.DataFrame(
        {
            "Дата операции": ["01.12.2021"],
            "Категория": ["Еда"],
            "Статус": ["OK"],
        }
    )
    result_json: str = analyze_cashback_categories(bad_data, 2021, 12)
    result: Dict[str, Any] = json.loads(result_json)

    assert "error" in result
    assert result["error"] == "Bonus column not found"


def test_analyze_cashback_no_data_for_period(sample_data: pd.DataFrame) -> None:
    """Тест, если за указанный период нет транзакций"""
    result: str = analyze_cashback_categories(sample_data, 2010, 1)
    assert result == "{}"


def test_analyze_cashback_categories_exception() -> None:
    """
    Тест проверяет обработку исключений (блок except).
    """
    result_json = analyze_cashback_categories(123, 2021, 12)  # type: ignore
    result = json.loads(result_json)
    assert "error" in result
    assert "object has no attribute" in result["error"]
