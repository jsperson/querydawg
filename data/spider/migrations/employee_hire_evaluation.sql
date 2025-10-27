-- Migration SQL for employee_hire_evaluation
-- Generated: 2025-10-22T12:09:48.714756
-- Source: /home/developer/source/querydawg/data/spider/database/employee_hire_evaluation/employee_hire_evaluation.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS employee_hire_evaluation;

-- Table: employee
CREATE TABLE employee_hire_evaluation.employee (
    Employee_ID BIGINT,
    Name TEXT,
    Age BIGINT,
    City TEXT,
    PRIMARY KEY (Employee_ID)
);

-- Table: shop
CREATE TABLE employee_hire_evaluation.shop (
    Shop_ID BIGINT,
    Name TEXT,
    Location TEXT,
    District TEXT,
    Number_products BIGINT,
    Manager_name TEXT,
    PRIMARY KEY (Shop_ID)
);

-- Table: hiring
CREATE TABLE employee_hire_evaluation.hiring (
    Shop_ID BIGINT,
    Employee_ID BIGINT,
    Start_from TEXT,
    Is_full_time TEXT,
    PRIMARY KEY (Employee_ID)
);

-- Table: evaluation
CREATE TABLE employee_hire_evaluation.evaluation (
    Employee_ID TEXT,
    Year_awarded TEXT,
    Bonus DOUBLE PRECISION,
    PRIMARY KEY (Employee_ID, Year_awarded)
);

-- Data migration
-- employee: 10 rows
INSERT INTO employee_hire_evaluation.employee (Employee_ID, Name, Age, City) VALUES
    (1, 'George Chuter', 23, 'Bristol'),
    (2, 'Lee Mears', 29, 'Bath'),
    (3, 'Mark Regan', 43, 'Bristol'),
    (4, 'Jason Hobson', 30, 'Bristol'),
    (5, 'Tim Payne', 29, 'Wasps'),
    (6, 'Andrew Sheridan', 28, 'Sale'),
    (7, 'Matt Stevens', 29, 'Bath'),
    (8, 'Phil Vickery', 40, 'Wasps'),
    (9, 'Steve Borthwick', 32, 'Bath'),
    (10, 'Louis Deacon', 36, 'Leicester');

-- shop: 9 rows
INSERT INTO employee_hire_evaluation.shop (Shop_ID, Name, Location, District, Number_products, Manager_name) VALUES
    (1, 'FC Haka', 'Valkeakoski', 'Tehtaan kenttä', 3516, 'Olli Huttunen'),
    (2, 'HJK', 'Helsinki', 'Finnair Stadium', 10770, 'Antti Muurinen'),
    (3, 'FC Honka', 'Espoo', 'Tapiolan Urheilupuisto', 6000, 'Mika Lehkosuo'),
    (4, 'FC Inter', 'Turku', 'Veritas Stadion', 10000, 'Job Dragtsma'),
    (5, 'FF Jaro', 'Jakobstad', 'Jakobstads Centralplan', 5000, 'Mika Laurikainen'),
    (6, 'FC KooTeePee', 'Kotka', 'Arto Tolsa Areena', 4780, 'Tommi Kautonen'),
    (7, 'KuPS', 'Kuopio', 'Magnum Areena', 3500, 'Kai Nyyssönen'),
    (8, 'FC Lahti', 'Lahti', 'Lahden Stadion', 15000, 'Ilkka Mäkelä'),
    (9, 'IFK Mariehamn', 'Mariehamn', 'Wiklöf Holding Arena', 1600, 'Pekka Lyyski');

-- hiring: 7 rows
INSERT INTO employee_hire_evaluation.hiring (Shop_ID, Employee_ID, Start_from, Is_full_time) VALUES
    (1, 1, '2009', 'T'),
    (1, 2, '2003', 'T'),
    (8, 3, '2011', 'F'),
    (4, 4, '2012', 'T'),
    (5, 5, '2013', 'T'),
    (2, 6, '2010', 'F'),
    (6, 7, '2008', 'T');

-- evaluation: 6 rows
INSERT INTO employee_hire_evaluation.evaluation (Employee_ID, Year_awarded, Bonus) VALUES
    ('1', '2011', 3000.0),
    ('2', '2015', 3200.0),
    ('1', '2016', 2900.0),
    ('4', '2017', 3200.0),
    ('7', '2018', 3200.0),
    ('10', '2016', 4000.0);


-- Foreign key constraints (added after data load)
ALTER TABLE employee_hire_evaluation.hiring
    ADD CONSTRAINT fk_hiring_employee_0
    FOREIGN KEY (Employee_ID)
    REFERENCES employee_hire_evaluation.employee (Employee_ID);
ALTER TABLE employee_hire_evaluation.hiring
    ADD CONSTRAINT fk_hiring_shop_1
    FOREIGN KEY (Shop_ID)
    REFERENCES employee_hire_evaluation.shop (Shop_ID);
ALTER TABLE employee_hire_evaluation.evaluation
    ADD CONSTRAINT fk_evaluation_employee_0
    FOREIGN KEY (Employee_ID)
    REFERENCES employee_hire_evaluation.employee (Employee_ID);
