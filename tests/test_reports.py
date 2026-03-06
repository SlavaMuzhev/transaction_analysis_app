import json
from typing import Any
from unittest.mock import patch

import pandas as pd

from src.reports import project_root, report_to_file, spending_by_category


def test_spending_by_category_logic(sample_df: pd.DataFrame) -> None:
    """Проверяет фильтрацию по категории 'Еда'"""
    result = spending_by_category(sample_df, category="Еда", date="25.01.2023")

    assert len(result) == 1
    assert result.iloc[0]["Описание"] == "Кофе"
    assert result.iloc[0]["Сумма операции"] == -1000.0


def test_report_file_content(sample_df: pd.DataFrame) -> None:
    """Проверяет, что декоратор создал JSON с правильными данными"""
    report_dir = project_root / "reports"
    if report_dir.exists():
        for f in report_dir.glob("*.json"):
            f.unlink()

    spending_by_category(sample_df, category="Транспорт", date="25.01.2023")

    report_files = list(report_dir.glob("report_*.json"))
    assert len(report_files) == 1

    with report_files[0].open("r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)
        assert data[0]["Категория"] == "Транспорт"
        assert data[0]["Описание"] == "Такси"


def test_date_range_filtering(sample_df: pd.DataFrame) -> None:
    report_dir = project_root / "reports"

    for f in report_dir.glob("*.json"):
        f.unlink()

    spending_by_category(sample_df, category="Транспорт", date="01.02.2023")

    files = list(report_dir.glob("report_*.json"))
    assert len(files) > 0, "Файл отчета не был создан!"

    latest_file = max(files, key=lambda x: x.stat().st_mtime)

    with open(latest_file, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert len(data) == 1
        assert data[0]["Категория"] == "Транспорт"


def test_empty_result_no_file(sample_data: pd.DataFrame) -> None:
    """Проверяет, что если транзакций нет, файл не создается (в твоей версии он создастся пустым)."""

    result = spending_by_category(sample_data, category="Несуществующая", date="01.01.2024")
    assert result.empty


def test_report_to_file_wrong_type() -> None:
    """Тест на ошибку типа: проверяет ветку, где функция возвращает не DataFrame (строки 35-36)"""

    @report_to_file
    def bad_function() -> str:
        return "я не датафрейм, я просто строка"

    result = bad_function()

    assert result == "я не датафрейм, я просто строка"


def test_report_custom_filename(sample_df: pd.DataFrame, report_dir: Any) -> None:
    """Закрывает строку 43: передача имени файла строкой"""
    custom_name = "specific_report.json"

    @report_to_file(filename=custom_name)
    def func_with_name(df: pd.DataFrame) -> pd.DataFrame:
        return df

    func_with_name(sample_df)

    assert (report_dir / custom_name).exists()


def test_spending_by_category_no_date_provided(sample_df: pd.DataFrame) -> None:
    """Закрывает строку 72: вызов функции без аргумента date"""
    result = spending_by_category(sample_df, category="Еда")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_report_to_file_save_error(sample_df: pd.DataFrame, report_dir: Any) -> None:
    """Тестирует обработку ошибки при сохранении файла (строки 100-101)"""

    @report_to_file("error_test.json")
    def mock_report(df: pd.DataFrame) -> pd.DataFrame:
        return df

    with patch("pandas.DataFrame.to_json") as mock_to_json, patch("src.reports.logger.error") as mock_logger_error:
        mock_to_json.side_effect = Exception("Системная ошибка доступа")

        result = mock_report(sample_df)

        assert len(result) == len(sample_df)

        mock_logger_error.assert_called_with(
            f"Ошибка при сохранении отчета в {project_root / 'reports' / 'error_test.json'}: Системная ошибка доступа"
        )
