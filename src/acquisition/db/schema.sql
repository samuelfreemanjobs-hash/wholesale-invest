-- Deal Intelligence Vault (SQLite)

CREATE TABLE IF NOT EXISTS properties (
    property_id TEXT PRIMARY KEY,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'MI',
    zip_code TEXT,
    asking_price REAL,
    beds INTEGER,
    baths REAL,
    verification_status TEXT,
    pipeline_status TEXT,
    score_total REAL,
    priority_label TEXT,
    risk_class TEXT,
    hard_stop INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    snippet TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
);

CREATE TABLE IF NOT EXISTS buyers (
    buyer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    last_verified_at TEXT,
    active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detail TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
);

CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_score ON properties(score_total DESC);
CREATE INDEX IF NOT EXISTS idx_sources_property ON sources(property_id);