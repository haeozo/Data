-- shows определение

CREATE TABLE shows (
	show_uri TEXT NOT NULL,
	show_name TEXT NOT NULL,
	show_publisher TEXT,
	show_media_type TEXT,
	show_total_episodes INTEGER,
	CONSTRAINT shows_pk PRIMARY KEY (show_uri)
);

-- episodes определение

CREATE TABLE episodes (
	episode_uri TEXT NOT NULL,
	show_uri TEXT NOT NULL,
	episode_name TEXT NOT NULL,
	description TEXT,
	duration_ms INTEGER,
	explicit INTEGER,
	languages TEXT,
	release_date TEXT,
	CONSTRAINT episodes_pk PRIMARY KEY (episode_uri),
	CONSTRAINT episodes_shows_FK FOREIGN KEY (show_uri) REFERENCES shows(show_uri)
);

-- chart_records определение

CREATE TABLE chart_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    region TEXT NOT NULL,
    rank INTEGER NOT NULL,
    chart_rank_move INTEGER,
    episode_uri TEXT NOT NULL,
    FOREIGN KEY (episode_uri) REFERENCES episodes(episode_uri) ON DELETE CASCADE
);