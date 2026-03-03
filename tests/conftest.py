import pytest
import pandas as pd


@pytest.fixture
def sample_df():
    """Генерация тестового DataFrame с транзакциями"""
    df = pd.DataFrame({
        "Дата операции": ["01.01.2023 10:00:00", "15.01.2023 12:00:00", "20.01.2023 15:00:00"],
        "Номер карты": ["*1111", "*2222", "*1111"],
        "Сумма операции": [-1000.0, -500.0, -2000.0],
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Описание": ["Магнит", "Такси", "Пятерочка"]
    })
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df

@pytest.fixture
def mock_settings():
    """Данные для user_settings.json"""
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "TSLA"]
    }


@pytest.fixture
def mock_utils_data():
    """Фикстура с заготовленными данными от функций-помощников"""
    return {
        "greeting": '"Добрый день"',
        "cards": [{"last_digits": "1234", "total_spent": 1000.0, "cashback": 10.0}],
        "top": [{"date": "01.01.2023", "amount": 500.0, "category": "Еда", "description": "Тест"}],
        "market": {
            "currencies": [{"currency": "USD", "rate": 75.0}],
            "stocks": [{"stock": "AAPL", "price": 150.0}]
        }
    }

