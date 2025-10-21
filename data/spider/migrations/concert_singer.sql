-- Migration SQL for concert_singer
-- Generated: 2025-10-20T20:17:21.122227
-- Source: /home/developer/source/dataprism/data/spider/database/concert_singer/concert_singer.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS concert_singer;

-- Table: stadium
CREATE TABLE concert_singer.stadium (
    Stadium_ID BIGINT,
    Location TEXT,
    Name TEXT,
    Capacity BIGINT,
    Highest BIGINT,
    Lowest BIGINT,
    Average BIGINT,
    PRIMARY KEY (Stadium_ID)
);

-- Table: singer
CREATE TABLE concert_singer.singer (
    Singer_ID BIGINT,
    Name TEXT,
    Country TEXT,
    Song_Name TEXT,
    Song_release_year TEXT,
    Age BIGINT,
    Is_male TEXT,
    PRIMARY KEY (Singer_ID)
);

-- Table: concert
CREATE TABLE concert_singer.concert (
    concert_ID BIGINT,
    concert_Name TEXT,
    Theme TEXT,
    Stadium_ID TEXT,
    Year TEXT,
    PRIMARY KEY (concert_ID)
);

-- Table: singer_in_concert
CREATE TABLE concert_singer.singer_in_concert (
    concert_ID BIGINT,
    Singer_ID TEXT,
    PRIMARY KEY (concert_ID, Singer_ID)
);

-- Data migration
-- stadium: 9 rows
INSERT INTO concert_singer.stadium (Stadium_ID, Location, Name, Capacity, Highest, Lowest, Average) VALUES
    (1, 'Raith Rovers', 'Stark''s Park', 10104, 4812, 1294, 2106),
    (2, 'Ayr United', 'Somerset Park', 11998, 2363, 1057, 1477),
    (3, 'East Fife', 'Bayview Stadium', 2000, 1980, 533, 864),
    (4, 'Queen''s Park', 'Hampden Park', 52500, 1763, 466, 730),
    (5, 'Stirling Albion', 'Forthbank Stadium', 3808, 1125, 404, 642),
    (6, 'Arbroath', 'Gayfield Park', 4125, 921, 411, 638),
    (7, 'Alloa Athletic', 'Recreation Park', 3100, 1057, 331, 637),
    (9, 'Peterhead', 'Balmoor', 4000, 837, 400, 615),
    (10, 'Brechin City', 'Glebe Park', 3960, 780, 315, 552);

-- singer: 6 rows
INSERT INTO concert_singer.singer (Singer_ID, Name, Country, Song_Name, Song_release_year, Age, Is_male) VALUES
    (1, 'Joe Sharp', 'Netherlands', 'You', '1992', 52, 'F'),
    (2, 'Timbaland', 'United States', 'Dangerous', '2008', 32, 'T'),
    (3, 'Justin Brown', 'France', 'Hey Oh', '2013', 29, 'T'),
    (4, 'Rose White', 'France', 'Sun', '2003', 41, 'F'),
    (5, 'John Nizinik', 'France', 'Gentleman', '2014', 43, 'T'),
    (6, 'Tribal King', 'France', 'Love', '2016', 25, 'T');

-- concert: 6 rows
INSERT INTO concert_singer.concert (concert_ID, concert_Name, Theme, Stadium_ID, Year) VALUES
    (1, 'Auditions', 'Free choice', '1', '2014'),
    (2, 'Super bootcamp', 'Free choice 2', '2', '2014'),
    (3, 'Home Visits', 'Bleeding Love', '2', '2015'),
    (4, 'Week 1', 'Wide Awake', '10', '2014'),
    (5, 'Week 1', 'Happy Tonight', '9', '2015'),
    (6, 'Week 2', 'Party All Night', '7', '2015');

-- singer_in_concert: 10 rows
INSERT INTO concert_singer.singer_in_concert (concert_ID, Singer_ID) VALUES
    (1, '2'),
    (1, '3'),
    (1, '5'),
    (2, '3'),
    (2, '6'),
    (3, '5'),
    (4, '4'),
    (5, '6'),
    (5, '3'),
    (6, '2');


-- Foreign key constraints (added after data load)
ALTER TABLE concert_singer.concert
    ADD CONSTRAINT fk_concert_stadium_0
    FOREIGN KEY (Stadium_ID)
    REFERENCES concert_singer.stadium (Stadium_ID);
ALTER TABLE concert_singer.singer_in_concert
    ADD CONSTRAINT fk_singer_in_concert_singer_0
    FOREIGN KEY (Singer_ID)
    REFERENCES concert_singer.singer (Singer_ID);
ALTER TABLE concert_singer.singer_in_concert
    ADD CONSTRAINT fk_singer_in_concert_concert_1
    FOREIGN KEY (concert_ID)
    REFERENCES concert_singer.concert (concert_ID);
