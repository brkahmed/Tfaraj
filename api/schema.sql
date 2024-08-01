CREATE TABLE anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mal_id INT UNIQUE,
    name TEXT UNIQUE
);

CREATE TABLE episode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number FLOAT,
    anime_id INT,
    FOREIGN KEY(anime_id) REFERENCES anime(id)
);

CREATE TABLE source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    url TEXT,
    episode_id INT,
    FOREIGN KEY(episode_id) REFERENCES episode(id)
);

CREATE INDEX idx_anime_id ON anime(id);
CREATE INDEX idx_anime_name ON anime(name);
CREATE INDEX idx_episode_id ON episode(id);
CREATE INDEX idx_episode_anime_id ON episode(anime_id);
CREATE INDEX idx_source_episode_id ON source(episode_id);
