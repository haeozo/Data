from pathlib import Path

from io_utils import (
    create_debug_slice,
    detect_encoding,
    get_columns,
    get_file_format,
    get_file_size,
    read_first_rows,
)

file_path = "data/raw/top_podcasts.csv"
debug_file_path = "data/interim/top_podcasts_debug.csv"


file_size = get_file_size(file_path)
file_format = get_file_format(file_path)
encoding = detect_encoding(file_path)
columns = get_columns(file_path, encoding)

print(f"Размер файла: {file_size:.2f} МБ")
print(f"Формат файла: {file_format}")
print(f"Кодировка: {encoding}")

print("\nСтолбцы:")
for column in columns:
    print(column)

print("\nПервые 100 строк:")
read_first_rows(file_path, encoding)


create_debug_slice(
    file_path,
    debug_file_path,
    encoding,
)

print(f"\nОтладочный срез создан: {debug_file_path}")