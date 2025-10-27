-- Migration SQL for museum_visit
-- Generated: 2025-10-22T12:09:51.122198
-- Source: /home/developer/source/querydawg/data/spider/database/museum_visit/museum_visit.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS museum_visit;

-- Table: museum
CREATE TABLE museum_visit.museum (
    Museum_ID BIGINT,
    Name TEXT,
    Num_of_Staff BIGINT,
    Open_Year TEXT,
    PRIMARY KEY (Museum_ID)
);

-- Table: visitor
CREATE TABLE museum_visit.visitor (
    ID BIGINT,
    Name TEXT,
    Level_of_membership BIGINT,
    Age BIGINT,
    PRIMARY KEY (ID)
);

-- Table: visit
CREATE TABLE museum_visit.visit (
    Museum_ID BIGINT,
    visitor_ID TEXT,
    Num_of_Ticket BIGINT,
    Total_spent DOUBLE PRECISION,
    PRIMARY KEY (Museum_ID, visitor_ID)
);

-- Data migration
-- museum: 8 rows
INSERT INTO museum_visit.museum (Museum_ID, Name, Num_of_Staff, Open_Year) VALUES
    (1, 'Plaza Museum', 62, '2000'),
    (2, 'Capital Plaza Museum', 25, '2012'),
    (3, 'Jefferson Development Museum', 18, '2010'),
    (4, 'Willow Grande Museum', 17, '2011'),
    (5, 'RiverPark Museum', 16, '2008'),
    (6, 'Place Tower Museum', 16, '2008'),
    (7, 'Central City District Residential Museum', 15, '2010'),
    (8, 'ZirMed Gateway Museum', 12, '2009');

-- visitor: 6 rows
INSERT INTO museum_visit.visitor (ID, Name, Level_of_membership, Age) VALUES
    (1, 'Gonzalo Higuaín ', 8, 35),
    (2, 'Guti Midfielder', 5, 28),
    (3, 'Arjen Robben', 1, 27),
    (4, 'Raúl Brown', 2, 56),
    (5, 'Fernando Gago', 6, 36),
    (6, 'Rafael van der Vaart', 1, 25);

-- visit: 6 rows
INSERT INTO museum_visit.visit (Museum_ID, visitor_ID, Num_of_Ticket, Total_spent) VALUES
    (1, '5', 20, 320.14),
    (2, '5', 4, 89.98),
    (4, '3', 10, 320.44),
    (2, '3', 24, 209.98),
    (4, '6', 3, 20.44),
    (8, '6', 2, 19.98);


-- Foreign key constraints (added after data load)
ALTER TABLE museum_visit.visit
    ADD CONSTRAINT fk_visit_visitor_0
    FOREIGN KEY (visitor_ID)
    REFERENCES museum_visit.visitor (ID);
ALTER TABLE museum_visit.visit
    ADD CONSTRAINT fk_visit_museum_1
    FOREIGN KEY (Museum_ID)
    REFERENCES museum_visit.museum (Museum_ID);
