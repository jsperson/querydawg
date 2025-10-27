-- Migration SQL for network_1
-- Generated: 2025-10-22T12:09:43.460158
-- Source: /home/developer/source/querydawg/data/spider/database/network_1/network_1.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS network_1;

-- Table: Highschooler
CREATE TABLE network_1.Highschooler (
    ID BIGINT,
    name TEXT,
    grade BIGINT,
    PRIMARY KEY (ID)
);

-- Table: Friend
CREATE TABLE network_1.Friend (
    student_id BIGINT,
    friend_id BIGINT,
    PRIMARY KEY (student_id, friend_id)
);

-- Table: Likes
CREATE TABLE network_1.Likes (
    student_id BIGINT,
    liked_id BIGINT,
    PRIMARY KEY (student_id, liked_id)
);

-- Data migration
-- Highschooler: 16 rows
INSERT INTO network_1.Highschooler (ID, name, grade) VALUES
    (1510, 'Jordan', 9),
    (1689, 'Gabriel', 9),
    (1381, 'Tiffany', 9),
    (1709, 'Cassandra', 9),
    (1101, 'Haley', 10),
    (1782, 'Andrew', 10),
    (1468, 'Kris', 10),
    (1641, 'Brittany', 10),
    (1247, 'Alexis', 11),
    (1316, 'Austin', 11),
    (1911, 'Gabriel', 11),
    (1501, 'Jessica', 11),
    (1304, 'Jordan', 12),
    (1025, 'John', 12),
    (1934, 'Kyle', 12),
    (1661, 'Logan', 12);

-- Friend: 20 rows
INSERT INTO network_1.Friend (student_id, friend_id) VALUES
    (1510, 1381),
    (1510, 1689),
    (1689, 1709),
    (1381, 1247),
    (1709, 1247),
    (1689, 1782),
    (1782, 1468),
    (1782, 1316),
    (1782, 1304),
    (1468, 1101),
    (1468, 1641),
    (1101, 1641),
    (1247, 1911),
    (1247, 1501),
    (1911, 1501),
    (1501, 1934),
    (1316, 1934),
    (1934, 1304),
    (1304, 1661),
    (1661, 1025);

-- Likes: 10 rows
INSERT INTO network_1.Likes (student_id, liked_id) VALUES
    (1689, 1709),
    (1709, 1689),
    (1782, 1709),
    (1911, 1247),
    (1247, 1468),
    (1641, 1468),
    (1316, 1304),
    (1501, 1934),
    (1934, 1501),
    (1025, 1101);


-- Foreign key constraints (added after data load)
ALTER TABLE network_1.Friend
    ADD CONSTRAINT fk_Friend_Highschooler_0
    FOREIGN KEY (friend_id)
    REFERENCES network_1.Highschooler (ID);
ALTER TABLE network_1.Friend
    ADD CONSTRAINT fk_Friend_Highschooler_1
    FOREIGN KEY (student_id)
    REFERENCES network_1.Highschooler (ID);
ALTER TABLE network_1.Likes
    ADD CONSTRAINT fk_Likes_Highschooler_0
    FOREIGN KEY (student_id)
    REFERENCES network_1.Highschooler (ID);
ALTER TABLE network_1.Likes
    ADD CONSTRAINT fk_Likes_Highschooler_1
    FOREIGN KEY (liked_id)
    REFERENCES network_1.Highschooler (ID);
