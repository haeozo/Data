import os
import time
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)


parquet_path = Path("../data/processed/clean.parquet")
if not parquet_path.exists():
  parquet_path = Path("data/processed/clean.parquet")

print("Загружаем данные из Parquet")
df = pd.read_parquet(parquet_path)
print(f"Всего строк в DataFrame: {len(df)}")



print("\nЗапуск способа 1: Пакетная вставка (to_sql)")
start_time = time.time()

try:
  # Очищаем таблицы перед тестом 
  with engine.begin() as conn:
    conn.execute(
        text(
            "TRUNCATE TABLE chart_records, episodes, shows RESTART IDENTITY"
            " CASCADE;"
        )
    )


  shows_df = df[
      [
          "show_uri",
          "show_name",
          "show_publisher",
          "show_media_type",
          "show_total_episodes",
      ]
  ].dropna(subset=["show_uri", "show_name"]).drop_duplicates(subset=["show_uri"])
  shows_df.to_sql("shows", engine, if_exists="append", index=False, chunksize=5000)
  valid_show_uris = set(shows_df["show_uri"])
 
  episodes_df = df[
      [
          "episode_uri",
          "show_uri",
          "episode_name",
          "description",
          "duration_ms",
          "explicit",
          "languages",
          "release_date",
      ]
  ].drop_duplicates(subset=["episode_uri"])
  episodes_df = episodes_df[episodes_df["show_uri"].isin(valid_show_uris)].copy()
  episodes_df["explicit"] = episodes_df["explicit"].fillna(False).astype(bool)  
  episodes_df.to_sql(
      "episodes", engine, if_exists="append", index=False, chunksize=5000
  )
  valid_episode_uris = set(episodes_df["episode_uri"])

  chart_df = df[["date", "region", "rank", "chart_rank_move", "episode_uri"]]
  chart_df = chart_df[chart_df["episode_uri"].isin(valid_episode_uris)]
  chart_df.to_sql(
      "chart_records", engine, if_exists="append", index=False, chunksize=5000
  )

  batch_duration = time.time() - start_time
  print(f"Пакетная вставка завершена за: {batch_duration:.2f} секунд.")

except Exception as e:
  print(f"Ошибка при пакетной вставке: {e}")



print("\nЗапуск способа 2: Потоковая загрузка")
start_time = time.time()

try:
  conn = psycopg2.connect(
      host=DB_HOST,
      database=DB_NAME,
      user=DB_USER,
      password=DB_PASSWORD,
      port=DB_PORT,
  )
  cursor = conn.cursor()


  cursor.execute(
      "TRUNCATE TABLE chart_records, episodes, shows RESTART IDENTITY CASCADE;"
  )
  conn.commit()

 
  shows_data = [
      (
          str(row.show_uri),
          str(row.show_name),
          str(row.show_publisher) if pd.notna(row.show_publisher) else None,
          str(row.show_media_type) if pd.notna(row.show_media_type) else None,
          int(row.show_total_episodes)
          if pd.notna(row.show_total_episodes)
          else None,
      )
      for row in df[
          [
              "show_uri",
              "show_name",
              "show_publisher",
              "show_media_type",
              "show_total_episodes",
          ]
      ]
      .drop_duplicates(subset=["show_uri"])
      .itertuples(index=False)
  ]
  execute_values(
      cursor,
      "INSERT INTO shows (show_uri, show_name, show_publisher, show_media_type,"
      " show_total_episodes) VALUES %s ON CONFLICT (show_uri) DO NOTHING",
      shows_data,
      page_size=5000,
  )


  episodes_data = [
      (
          str(row.episode_uri),
          str(row.show_uri),
          str(row.episode_name),
          str(row.description) if pd.notna(row.description) else None,
          int(row.duration_ms) if pd.notna(row.duration_ms) else None,
          bool(row.explicit) if pd.notna(row.explicit) else False,
          str(row.languages) if pd.notna(row.languages) else None,
          str(row.release_date) if pd.notna(row.release_date) else None,
      )
      for row in df[
          [
              "episode_uri",
              "show_uri",
              "episode_name",
              "description",
              "duration_ms",
              "explicit",
              "languages",
              "release_date",
          ]
      ]
      .drop_duplicates(subset=["episode_uri"])
      .itertuples(index=False)
  ]
  execute_values(
      cursor,
      "INSERT INTO episodes (episode_uri, show_uri, episode_name, description,"
      " duration_ms, explicit, languages, release_date) VALUES %s ON CONFLICT"
      " (episode_uri) DO NOTHING",
      episodes_data,
      page_size=5000,
  )


  chart_data = [
      (
          str(row.date),
          str(row.region),
          int(row.rank) if pd.notna(row.rank) else 0,
          str(row.chart_rank_move)
          if pd.notna(row.chart_rank_move)
          else None,
          str(row.episode_uri),
      )
      for row in df[
          ["date", "region", "rank", "chart_rank_move", "episode_uri"]
      ]
      .dropna(subset=["episode_uri"])
      .itertuples(index=False)
  ]
  execute_values(
      cursor,
      "INSERT INTO chart_records (date, region, rank, chart_rank_move,"
      " episode_uri) VALUES %s",
      chart_data,
      page_size=10000,
  )

  conn.commit()
  cursor.close()
  conn.close()

  stream_duration = time.time() - start_time
  print(f" Потоковая загрузка завершена за: {stream_duration:.2f} секунд.")

except Exception as e:  
  print(f"Ошибка при потоковой загрузке: {e}")