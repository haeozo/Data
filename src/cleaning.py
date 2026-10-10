import logging
import re

import pandas as pd

from .config import DEBUG_DATA_PATH, PROCESSED_DIR, RAW_DATA_PATH

logging.basicConfig(
    filename=PROCESSED_DIR / "cleaning.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)


def log_step(name, processed, changed=0, removed=0):
    msg = f"{name} | processed={processed} | changed={changed} | removed={removed}"
    logger.info(msg)
    print(msg)


def load_data():
    return pd.read_csv(DEBUG_DATA_PATH)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    old = list(df.columns)
    new = []
    for col in old:
        name = str(col).strip()
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
        name = name.lower()
        name = re.sub(r"\s+", "_", name)
        name = name.replace(".", "_")
        name = re.sub(r"[^a-z0-9_]", "", name)
        new.append(name)
    df.columns = new
    changed = sum(a != b for a, b in zip(old, new))
    log_step("2_clean_column_names", len(df), changed, 0)
    return df


def convert_types(df):
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["release_date"] = pd.to_datetime(
        df["release_date"], errors="coerce"
    )

    df["rank"] = pd.to_numeric(
        df["rank"], errors="coerce"
    ).astype("Int32")

    df["duration_ms"] = pd.to_numeric(
        df["duration_ms"], errors="coerce"
    ).astype("Int32")

    df["show_total_episodes"] = pd.to_numeric(
        df["show_total_episodes"], errors="coerce"
    )

    df["explicit"] = df["explicit"].astype("boolean")

    for col in [
        "episode_uri",
        "show_uri",
        "episode_name",
        "description",
        "show_name",
        "show_publisher",
        "region",
        "chart_rank_move",
        "languages",
        "show_media_type",
    ]:
        df[col] = df[col].astype("string")

    log_step("convert_types", len(df))
    return df


def replace_hidden_missing(df):
    df = df.copy()
    changed = 0
    bad_text = {"", "-", "--", "n/a", "na", "null", "unknown", "нет данных"}

    for col in df.select_dtypes(include=["string", "object"]).columns:
        norm = df[col].astype("string").str.strip().str.casefold()
        mask = norm.isin(bad_text)
        changed += int(mask.sum())
        df.loc[mask, col] = pd.NA

    for col, cond in [
        ("rank", df["rank"] == 0),
        ("duration_ms", df["duration_ms"] < 0),
        ("show_total_episodes", df["show_total_episodes"] < 0),
    ]:
        changed += int(cond.sum())
        df.loc[cond, col] = pd.NA

    today = pd.Timestamp.now().normalize()
    for col in ("date", "release_date"):
        bad = df[col].notna() & (df[col] > today)
        changed += int(bad.sum())
        df.loc[bad, col] = pd.NaT

    log_step("replace_hidden_missing", len(df), changed=changed)
    return df


def analyze_missing(df):
    missing = pd.DataFrame({
        "count": df.isna().sum(),
        "percent": (df.isna().mean() * 100).round(2),
    })
    by_region = (
        df.groupby("region", observed=True)
        .apply(lambda x: x.isna().mean().mean())
        .sort_values(ascending=False)
    )
    log_step("analyze_missing", len(df))
    return missing, by_region


def remove_duplicates(df):
    n = len(df)
    df = df.copy()
    df = df.drop_duplicates()
    df = df.sort_values("date")
    df = df.drop_duplicates(subset=["date", "episode_uri", "region"], keep="last")
    log_step("remove_duplicates", n, removed=n - len(df))
    return df


def normalize_categories(df, min_count=10):
    df = df.copy()
    changed = 0
    cols = ["region", "chart_rank_move", "languages", "show_media_type"]

    for col in cols:
        s = df[col].astype("string").str.strip().str.lower()
        changed += int((df[col].astype("string") != s).sum())
        df[col] = s
        
    df["show_media_type"] = df["show_media_type"].replace({
        "podcast": "audio",
        "audio": "audio",
        "video": "video",
    })

    for col in cols:
        rare = df[col].value_counts(dropna=True)
        rare = set(rare[rare < min_count].index)
        mask = df[col].notna() & df[col].isin(rare)
        changed += int(mask.sum())
        df.loc[mask, col] = "other"
        df[col] = df[col].astype("category")

    log_step("normalize_categories", len(df), changed=changed)
    return df


def clean_text(df, col="description"):
    df = df.copy()
    s = df[col].astype("string")
    s = s.str.replace(r"<[^>]*>", "", regex=True)
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    bad = s.str.casefold().isin({"", "-", "n/a", "unknown", "нет данных"})
    s = s.where(~bad, pd.NA)
    changed = int((df[col].astype("string") != s).sum())
    df[col] = s
    log_step("clean_text", len(df), changed=changed)
    return df


def normalize_numeric_units(df):
    # duration_ms уже в миллисекундах
    log_step("normalize_numeric_units", len(df))
    return df


def check_constraints(df):
    n = len(df)
    today = pd.Timestamp.now().normalize()
    bad = (
        (df["rank"].notna() & (df["rank"] <= 0))
        | (df["duration_ms"].notna() & (df["duration_ms"] < 0))
        | (df["show_total_episodes"].notna() & (df["show_total_episodes"] < 0))
        | (df["date"].notna() & (df["date"] > today))
        | (df["release_date"].notna() & (df["release_date"] > today))
        | (
            df["release_date"].notna()
            & df["date"].notna()
            & (df["release_date"] > df["date"])
        )
    )
    df = df.loc[~bad].copy()
    log_step("check_constraints", n, removed=int(bad.sum()))
    return df


def detect_outliers(df):
    rows = []
    for col in ["duration_ms", "show_total_episodes"]:
        x = df[col].dropna()
        if len(x) == 0:
            rows.append({"column": col, "iqr": 0, "zscore": 0, "both": 0})
            continue
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        iqr = q3 - q1
        iqr_bad = (x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)
        z = (x - x.mean()) / x.std() if x.std() > 0 else x * 0
        z_bad = z.abs() > 3
        both = iqr_bad & z_bad
        rows.append({
            "column": col,
            "iqr": int(iqr_bad.sum()),
            "zscore": int(z_bad.sum()),
            "both": int(both.sum()),
        })
    result = pd.DataFrame(rows)
    log_step("detect_outliers", len(df))
    return result


def save_clean_data(df):
    path = PROCESSED_DIR / "clean.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    log_step("save_clean_data", len(df))
    print("Сохранено:", path)
    return df