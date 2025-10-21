-- Migration SQL for singer
-- Generated: 2025-10-20T20:20:02.022562
-- Source: /home/developer/source/dataprism/data/spider/database/singer/singer.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS singer;

-- Table: singer
CREATE TABLE singer.singer (
    Singer_ID BIGINT,
    Name TEXT,
    Birth_Year DOUBLE PRECISION,
    Net_Worth_Millions DOUBLE PRECISION,
    Citizenship TEXT,
    PRIMARY KEY (Singer_ID)
);

-- Table: song
CREATE TABLE singer.song (
    Song_ID BIGINT,
    Title TEXT,
    Singer_ID BIGINT,
    Sales DOUBLE PRECISION,
    Highest_Position DOUBLE PRECISION,
    PRIMARY KEY (Song_ID)
);

-- Data migration
-- singer: 8 rows
INSERT INTO singer.singer (Singer_ID, Name, Birth_Year, Net_Worth_Millions, Citizenship) VALUES
    (1, 'Liliane Bettencourt', 1944.0, 30.0, 'France'),
    (2, 'Christy Walton', 1948.0, 28.8, 'United States'),
    (3, 'Alice Walton', 1949.0, 26.3, 'United States'),
    (4, 'Iris Fontbona', 1942.0, 17.4, 'Chile'),
    (5, 'Jacqueline Mars', 1940.0, 17.8, 'United States'),
    (6, 'Gina Rinehart', 1953.0, 17.0, 'Australia'),
    (7, 'Susanne Klatten', 1962.0, 14.3, 'Germany'),
    (8, 'Abigail Johnson', 1961.0, 12.7, 'United States');

-- song: 8 rows
INSERT INTO singer.song (Song_ID, Title, Singer_ID, Sales, Highest_Position) VALUES
    (1, 'Do They Know It''s Christmas', 1, 1094000.0, 1.0),
    (2, 'F**k It (I Don''t Want You Back)', 1, 552407.0, 1.0),
    (3, 'Cha Cha Slide', 2, 351421.0, 1.0),
    (4, 'Call on Me', 4, 335000.0, 1.0),
    (5, 'Yeah', 2, 300000.0, 1.0),
    (6, 'All This Time', 6, 292000.0, 1.0),
    (7, 'Left Outside Alone', 5, 275000.0, 3.0),
    (8, 'Mysterious Girl', 7, 261000.0, 1.0);


-- Foreign key constraints (added after data load)
ALTER TABLE singer.song
    ADD CONSTRAINT fk_song_singer_0
    FOREIGN KEY (Singer_ID)
    REFERENCES singer.singer (Singer_ID);
