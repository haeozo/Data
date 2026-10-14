
import os
import time

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "podcasts_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=DB_PORT,
)
cursor = conn.cursor()


start_date = "2024-09-01"
end_date = "2024-09-07"

queries = {
    "1. Подсчет записей (COUNT)": "SELECT COUNT(*) FROM chart_records;",
    "2. Агрегирование по регионам (GROUP BY)": (
        "SELECT region, COUNT(*) FROM chart_records GROUP BY region;"
    ),
    "3. Выборка по диапазону дат (BETWEEN)": (
        f"SELECT * FROM chart_records WHERE date BETWEEN '{start_date}' AND"
        f" '{end_date}';"
    ),
}

print("Время запросов PostgreSQL")
for name, sql in queries.items():
  start_time = time.time()
  cursor.execute(sql)
  cursor.fetchall()
  elapsed = time.time() - start_time
  print(f"{name}: {elapsed:.6f} сек.")

cursor.close()
conn.close()