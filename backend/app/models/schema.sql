PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS film_stocks (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS cameras (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS lenses (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS film_rolls (
 id INTEGER PRIMARY KEY AUTOINCREMENT, roll_number INTEGER NOT NULL UNIQUE CHECK(roll_number > 0),
 title TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
 film_stock_id INTEGER NOT NULL REFERENCES film_stocks(id) ON DELETE RESTRICT,
 camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
 shot_iso INTEGER, started_at TEXT, finished_at TEXT, location TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'shooting' CHECK(status IN ('shooting','finished','developed','scanned','archived')),
 expected_frames INTEGER NOT NULL DEFAULT 36, actual_frames INTEGER NOT NULL DEFAULT 0,
 cover_photo_id INTEGER REFERENCES roll_photos(id) ON DELETE SET NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS film_roll_lenses (
 roll_id INTEGER NOT NULL REFERENCES film_rolls(id) ON DELETE CASCADE,
 lens_id INTEGER NOT NULL REFERENCES lenses(id) ON DELETE RESTRICT, PRIMARY KEY(roll_id, lens_id)
);
CREATE TABLE IF NOT EXISTS developments (
 id INTEGER PRIMARY KEY, roll_id INTEGER NOT NULL UNIQUE REFERENCES film_rolls(id) ON DELETE CASCADE,
 method TEXT NOT NULL DEFAULT 'lab', lab_name TEXT NOT NULL DEFAULT '', process TEXT NOT NULL DEFAULT '',
 developer TEXT NOT NULL DEFAULT '', temperature_c REAL, development_time_sec INTEGER,
 push_pull REAL NOT NULL DEFAULT 0, developed_at TEXT, cost REAL, currency TEXT NOT NULL DEFAULT 'CNY', notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS scans (
 id INTEGER PRIMARY KEY, roll_id INTEGER NOT NULL UNIQUE REFERENCES film_rolls(id) ON DELETE CASCADE,
 method TEXT NOT NULL DEFAULT 'lab', lab_name TEXT NOT NULL DEFAULT '', scanner_model TEXT NOT NULL DEFAULT '',
 resolution_width INTEGER, resolution_height INTEGER, file_format TEXT NOT NULL DEFAULT 'JPEG',
 scanned_at TEXT, cost REAL, currency TEXT NOT NULL DEFAULT 'CNY', notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS roll_photos (
 id INTEGER PRIMARY KEY AUTOINCREMENT, roll_id INTEGER NOT NULL REFERENCES film_rolls(id) ON DELETE CASCADE,
 frame_number INTEGER NOT NULL, file_path TEXT NOT NULL UNIQUE, thumbnail_path TEXT NOT NULL UNIQUE,
 original_filename TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, file_size INTEGER NOT NULL,
 caption TEXT NOT NULL DEFAULT '', is_cover INTEGER NOT NULL DEFAULT 0 CHECK(is_cover IN (0,1)),
 is_favorite INTEGER NOT NULL DEFAULT 0 CHECK(is_favorite IN (0,1)), sort_order INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS photos_roll_order ON roll_photos(roll_id, sort_order);
CREATE INDEX IF NOT EXISTS rolls_date ON film_rolls(started_at);
PRAGMA user_version = 1;
