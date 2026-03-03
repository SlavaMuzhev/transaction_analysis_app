import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """Создает тестовый DataFrame с транзакциями"""
    return pd.DataFrame(
        {
            "Дата операции": ["01.01.2023 10:00:00", "15.01.2023 12:00:00", "20.01.2023 15:00:00"],
            "Номер карты": ["*1111", "*1111", "*2222"],
            "Сумма операции": [-1000.0, -2000.0, -500.0],
            "Категория": ["Еда", "Супермаркеты", "Транспорт"],
            "Описание": ["Кофе", "Пятерочка", "Такси"],
        }
    )


@pytest.fixture
def mock_settings():
    """Имитирует содержимое user_settings.json"""
    return {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}


@pytest.fixture
def mock_utils_data():
    """Данные для имитации ответов всех функций utils в тестах views"""
    return {
        "greeting": "Добрый день",
        "cards": [{"last_digits": "1234", "total_spent": 1000.0, "cashback": 10.0}],
        "top_transactions": [{"date": "01.01.2023", "amount": 500.0, "category": "Еда", "description": "Кофе"}],
        "market": {"currencies": [{"currency": "USD", "rate": 75.5}], "stocks": [{"stock": "AAPL", "price": 150.0}]},
    }


@pytest.fixture
def mock_utils_data_with_minus():
    return {
        "Дата операции": pd.to_datetime(
            ["2023-10-01", "2023-10-05", "2023-10-02", "2023-10-10", "2023-10-08", "2023-10-07"]
        ),
        "Сумма операции": [100.0, -5000.0, 200.0, 300.0, 400.0, 50.0],
        "Категория": ["Еда", "Переводы", "Транспорт", "Сервисы", "Спорт", "Связь"],
        "Описание": ["Обед", "Другу", "Такси", "Подписка", "Зал", "МТС"],
    }
