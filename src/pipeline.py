import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from src.cleaning import (
    analyze_missing,
    check_constraints,
    clean_column_names,
    clean_text,
    convert_types,
    detect_outliers,
    normalize_categories,
    normalize_numeric_units,
    remove_duplicates,
    replace_hidden_missing,
)
from src.config import DEBUG_DATA_PATH, PROCESSED_DIR, RAW_DATA_PATH

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=PROCESSED_DIR / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)


def run_pipeline(input_path: Path, output_path: Path, step: str = None):
    logger.info(f"Запуск пайплайна. Входной файл: {input_path}")
    print(f"Загрузка данных из: {input_path}")

    
    if not input_path.exists():
        err_msg = f"Критическая ошибка: файл не найден -> {input_path}"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    
    try:
        df = pd.read_csv(input_path, on_bad_lines="skip")
    except Exception as e:
        err_msg = f"Ошибка чтения CSV (неверный формат или поврежденные строки): {e}"
        logger.error(err_msg)
        raise ValueError(err_msg)

    initial_len = len(df)
    print(f"Исходное количество строк: {initial_len}")

    
    if step:
        print( f"выполнение отдельного этапа: {step}" )
        if step == "clean_column_names":
            return clean_column_names(df)
        elif step == "convert_types":
            return convert_types(df)
       
        else:
            raise ValueError(f"Неизвестный шаг: {step}")


    try:
        df = clean_column_names(df)
        df = convert_types(df)
        df = replace_hidden_missing(df)
        analyze_missing(df)
        df = remove_duplicates(df)
        df = normalize_categories(df)
        df = clean_text(df)
        df = normalize_numeric_units(df)
        df = check_constraints(df)
        detect_outliers(df)


        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        final_len = len(df)
        logger.info(f"Пайплайн успешно выполнен. Итого строк: {final_len}")
        print(f"Результат успешно сохранен в: {output_path}")
        print(f"Было строк: {initial_len}, Стало: {final_len}")

    except Exception as e:
        logger.error(f"Ошибка в процессе выполнения пайплайна: {e}")
        print(f"Ошибка во время обработки: {e}")
        raise e

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Конвейер очистки данных (Pipeline)")
    parser.add_argument("--input", type=str, help="Путь к исходному CSV файлу")
    parser.add_argument("--output", type=str, help="Путь для сохранения Parquet файла")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "debug"],
        default="full",
        help="Режим работы: full (основной файл) или debug (срез)",
    )
    parser.add_argument("--step", type=str, default=None, help="Запуск только отдельного этапа")

    args = parser.parse_args()


    if args.input:
        in_path = Path(args.input)
    else:
        in_path = RAW_DATA_PATH if args.mode == "full" else DEBUG_DATA_PATH

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = PROCESSED_DIR / "clean_cli.parquet"

    run_pipeline(in_path, out_path, step=args.step)