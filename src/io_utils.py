import csv
import os
from pathlib import Path

from charset_normalizer import from_bytes


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


def read_first_rows(file_path, encoding, rows_count=100):
    with open(file_path, "r", encoding=encoding, newline="") as file:
        reader = csv.reader(file)

        for row_number, row in enumerate(reader):
            if row_number >= rows_count:
                break

            print(row)


def get_columns(file_path, encoding):
    with open(file_path, "r", encoding=encoding, newline="") as file:

        reader = csv.reader(file)

        return next(reader)

def create_debug_slice(file_path, output_path, encoding, rows_count=200_000):
    with (
        open(file_path, "r", encoding=encoding, newline="") as source_file,
        open(output_path, "w", encoding=encoding, newline="") as output_file,
    ):
        reader = csv.reader(source_file)
        writer = csv.writer(output_file)

        for row_number, row in enumerate(reader):
            if row_number >= rows_count:
                break

            writer.writerow(row)


