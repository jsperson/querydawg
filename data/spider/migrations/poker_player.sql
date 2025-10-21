-- Migration SQL for poker_player
-- Generated: 2025-10-20T20:19:58.518000
-- Source: /home/developer/source/dataprism/data/spider/database/poker_player/poker_player.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS poker_player;

-- Table: poker_player
CREATE TABLE poker_player.poker_player (
    Poker_Player_ID BIGINT,
    People_ID BIGINT,
    Final_Table_Made DOUBLE PRECISION,
    Best_Finish DOUBLE PRECISION,
    Money_Rank DOUBLE PRECISION,
    Earnings DOUBLE PRECISION,
    PRIMARY KEY (Poker_Player_ID)
);

-- Table: people
CREATE TABLE poker_player.people (
    People_ID BIGINT,
    Nationality TEXT,
    Name TEXT,
    Birth_Date TEXT,
    Height DOUBLE PRECISION,
    PRIMARY KEY (People_ID)
);

-- Data migration
-- poker_player: 5 rows
INSERT INTO poker_player.poker_player (Poker_Player_ID, People_ID, Final_Table_Made, Best_Finish, Money_Rank, Earnings) VALUES
    (1, 1, 42.0, 1.0, 68.0, 476090.0),
    (2, 2, 10.0, 2.0, 141.0, 189233.0),
    (3, 5, 21.0, 1.0, 166.0, 104871.0),
    (4, 6, 19.0, 2.0, 58.0, 596462.0),
    (5, 7, 26.0, 3.0, 154.0, 142800.0);

-- people: 7 rows
INSERT INTO poker_player.people (People_ID, Nationality, Name, Birth_Date, Height) VALUES
    (1, 'Russia', 'Aleksey Ostapenko', 'May 26, 1986', 207.0),
    (2, 'Bulgaria', 'Teodor Salparov', 'August 16, 1982', 182.0),
    (3, 'Russia', 'Roman Bragin', 'April 17, 1987', 187.0),
    (4, 'Russia', 'Sergey Grankin', 'January 22, 1987', 193.0),
    (5, 'Russia', 'Yevgeni Sivozhelez', 'August 8, 1986', 196.0),
    (6, 'Russia', 'Maksim Botin', 'July 14, 1983', 194.0),
    (7, 'Russia', 'Semen Poltavskiy', 'February 8, 1981', 205.0);


-- Foreign key constraints (added after data load)
ALTER TABLE poker_player.poker_player
    ADD CONSTRAINT fk_poker_player_people_0
    FOREIGN KEY (People_ID)
    REFERENCES poker_player.people (People_ID);
