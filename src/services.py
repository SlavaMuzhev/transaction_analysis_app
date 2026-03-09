import json
import logging
from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent
log_dir = project_root / "logs"
log_file_path = log_dir / "service.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(filename=log_file_path, mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def analyze_cashback_categories(data: pd.DataFrame, year: int, month: int) -> str:
    """
    Анализирует выгоду по категориям кешбэка за определенный месяц и год
    """
    try:
        if data is None or data.empty:
            return json.dumps({}, ensure_ascii=False)

        df = data.copy()

        bonus_col = [c for c in df.columns if "Бонус" in c]
        if not bonus_col:
            logger.error(f"Колонка с бонусами не найдена. Доступные: {list(df.columns)}")
            return json.dumps({"error": "Bonus column not found"}, ensure_ascii=False)

        target_col = bonus_col[0]

        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")

        mask = (df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month) & (df["Статус"] == "OK")
        filtered_df = df[mask].copy()

        if filtered_df.empty:
            return json.dumps({}, ensure_ascii=False)

        result = filtered_df.groupby("Категория")[target_col].sum().fillna(0).round().astype(int).to_dict()

        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА ПРИ АНАЛИЗЕ: {str(e)}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
