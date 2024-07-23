CREATE TABLE IF NOT EXISTS targets (
    target_id SERIAL PRIMARY KEY,
    ip_or_url TEXT NOT NULL,
    alias TEXT,
    UNIQUE (ip_or_url)
);

CREATE TABLE IF NOT EXISTS ping_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    target_id INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    FOREIGN KEY (target_id) REFERENCES targets (target_id)
);

CREATE TABLE IF NOT EXISTS ping_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    target_id INTEGER NOT NULL,
    rtt_min REAL,
    rtt_max REAL,
    rtt_avg REAL,
    FOREIGN KEY (target_id) REFERENCES targets (target_id)
);
