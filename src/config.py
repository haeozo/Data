from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"


RAW_DATA_PATH = RAW_DIR / "top_podcasts.csv"
DEBUG_DATA_PATH = INTERIM_DIR / "top_podcasts_debug.csv"




DATA_SCHEMA = {
    "date": "datetime",
    "rank": "int32",
    "region": "category",
    "chartRankMove": "category",
    "episodeUri": "string",
    "showUri": "string",
    "episodeName": "string",
    "description": "string",
    "show.name": "string",
    "show.publisher": "string",
    "duration_ms": "int32",
    "explicit": "boolean",
    "languages": "category",
}