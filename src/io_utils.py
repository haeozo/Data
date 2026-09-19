import os
from pathlib import Path

from charset_normalizer import from_bytes

file_path = "data/raw/top_podcasts.csv"


def get_file_size(file_path):
        file_size_bytes = os.path.getsize(file_path)
        file_size_megabytes = file_size_bytes / (1024 ** 2)
        return file_size_megabytes


def get_file_format(file_path):
        file_format = Path(file_path)
        return file_format.suffix


def detect_encoding(file_path):
        with open(file_path, "rb") as file:
                sample = file.read(100_000)
        result = from_bytes(sample).best()
        if result is None:
                return None
        return result.encoding

print(f"Размер файла: {get_file_size(file_path):.2f} МБ")
print(f"Формат файла : {get_file_format(file_path)}")

