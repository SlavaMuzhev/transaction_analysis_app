import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import pandas as pd

project_root = Path(__file__).resolve().parent.parent
log_dir = project_root / "logs"
log_file_path = log_dir / "reports.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(filename=log_file_path, mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


T = TypeVar("T", bound=pd.DataFrame)


def report_to_file(filename: Optional[str | Callable] = None) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            params_log = json.dumps(kwargs, ensure_ascii=False, default=str)
            logger.debug(f"Функция {func.__name__} вызвана с аргументами: {params_log}")

            result = func(*args, **kwargs)

            if not isinstance(result, pd.DataFrame):
                logger.error(f"Функция {func.__name__} вернула {type(result)} вместо pd.DataFrame. Отчет не сохранен.")
                return result

            df_to_save = result.copy()
            for col in df_to_save.select_dtypes(include=["datetime", "datetimetz"]).columns:
                df_to_save[col] = df_to_save[col].dt.strftime("%d.%m.%Y %H:%M:%S")

            if filename and isinstance(filename, str):
                file_name = filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"report_{timestamp}.json"

            target_file = project_root / "reports" / file_name

            try:
                df_to_save.to_json(target_file, orient="records", force_ascii=False, indent=4)
                logger.debug(f"Функция {func.__name__} успешно сохранила отчет в {target_file}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчета в {target_file}: {e}")

            return result

        return wrapper

    if callable(filename):
        return decorator(filename)
    return decorator


@report_to_file
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    logger.debug(f"Запуск отчета по категории: {category}, дата отсечки: {date or 'текущая'}")

    if date:
        end_date = pd.to_datetime(date, dayfirst=True)
    else:
        end_date = pd.Timestamp(datetime.now())

    start_date = end_date - pd.DateOffset(months=3)

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    filtered_df = df[
        (df["Категория"] == category) & (df["Дата операции"] <= end_date) & (df["Дата операции"] >= start_date)
    ]

    logger.info(f"Найдено транзакций: {len(filtered_df)}")
    return filtered_df
