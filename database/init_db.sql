CREATE TABLE IF NOT EXISTS ping_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    target_id INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    FOREIGN KEY (target_id) REFERENCES targets (target_id)
);

CREATE TABLE IF NOT EXISTS ping_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    target_id INTEGER NOT NULL,
    rtt_min REAL,
    rtt_max REAL,
    rtt_avg REAL,
    FOREIGN KEY (target_id) REFERENCES targets (target_id)
);


CREATE TABLE IF NOT EXISTS targets (
    target_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_or_url TEXT NOT NULL,
    alias TEXT,
    UNIQUE (ip_or_url)
)