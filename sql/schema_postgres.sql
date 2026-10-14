-- 1. Таблица шоу
CREATE TABLE shows (
    show_uri VARCHAR(255) PRIMARY KEY,
    show_name TEXT NOT NULL,
    show_publisher TEXT,
    show_media_type TEXT,
    show_total_episodes INTEGER
);

-- 2. Таблица эпизодов
CREATE TABLE episodes (
    episode_uri VARCHAR(255) PRIMARY KEY,
    show_uri VARCHAR(255) NOT NULL REFERENCES shows(show_uri),
    episode_name TEXT NOT NULL,
    description TEXT,
    duration_ms INTEGER,
    explicit INTEGER,
    languages TEXT,
    release_date TEXT
);

-- 3. Таблица фактов чартов
CREATE TABLE chart_records (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    region VARCHAR(10) NOT NULL,
    rank INTEGER NOT NULL,
    chart_rank_move INTEGER,
    episode_uri VARCHAR(255) NOT NULL REFERENCES episodes(episode_uri) ON DELETE CASCADE
);