-- Migration SQL for pets_1
-- Generated: 2025-10-22T12:09:45.874811
-- Source: /home/developer/source/querydawg/data/spider/database/pets_1/pets_1.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS pets_1;

-- Table: Student
CREATE TABLE pets_1.Student (
    StuID BIGINT,
    LName VARCHAR(10),
    Fname VARCHAR(10),
    Age BIGINT,
    Sex VARCHAR(10),
    Major BIGINT,
    Advisor BIGINT,
    city_code VARCHAR(10),
    PRIMARY KEY (StuID)
);

-- Table: Has_Pet
CREATE TABLE pets_1.Has_Pet (
    StuID BIGINT,
    PetID BIGINT
);

-- Table: Pets
CREATE TABLE pets_1.Pets (
    PetID BIGINT,
    PetType VARCHAR(10),
    pet_age BIGINT,
    weight DOUBLE PRECISION,
    PRIMARY KEY (PetID)
);

-- Data migration
-- Student: 34 rows
INSERT INTO pets_1.Student (StuID, LName, Fname, Age, Sex, Major, Advisor, city_code) VALUES
    (1001, 'Smith', 'Linda', 18, 'F', 600, 1121, 'BAL'),
    (1002, 'Kim', 'Tracy', 19, 'F', 600, 7712, 'HKG'),
    (1003, 'Jones', 'Shiela', 21, 'F', 600, 7792, 'WAS'),
    (1004, 'Kumar', 'Dinesh', 20, 'M', 600, 8423, 'CHI'),
    (1005, 'Gompers', 'Paul', 26, 'M', 600, 1121, 'YYZ'),
    (1006, 'Schultz', 'Andy', 18, 'M', 600, 1148, 'BAL'),
    (1007, 'Apap', 'Lisa', 18, 'F', 600, 8918, 'PIT'),
    (1008, 'Nelson', 'Jandy', 20, 'F', 600, 9172, 'BAL'),
    (1009, 'Tai', 'Eric', 19, 'M', 600, 2192, 'YYZ'),
    (1010, 'Lee', 'Derek', 17, 'M', 600, 2192, 'HOU'),
    (1011, 'Adams', 'David', 22, 'M', 600, 1148, 'PHL'),
    (1012, 'Davis', 'Steven', 20, 'M', 600, 7723, 'PIT'),
    (1014, 'Norris', 'Charles', 18, 'M', 600, 8741, 'DAL'),
    (1015, 'Lee', 'Susan', 16, 'F', 600, 8721, 'HKG'),
    (1016, 'Schwartz', 'Mark', 17, 'M', 600, 2192, 'DET'),
    (1017, 'Wilson', 'Bruce', 27, 'M', 600, 1148, 'LON'),
    (1018, 'Leighton', 'Michael', 20, 'M', 600, 1121, 'PIT'),
    (1019, 'Pang', 'Arthur', 18, 'M', 600, 2192, 'WAS'),
    (1020, 'Thornton', 'Ian', 22, 'M', 520, 7271, 'NYC'),
    (1021, 'Andreou', 'George', 19, 'M', 520, 8722, 'NYC'),
    (1022, 'Woods', 'Michael', 17, 'M', 540, 8722, 'PHL'),
    (1023, 'Shieber', 'David', 20, 'M', 520, 8722, 'NYC'),
    (1024, 'Prater', 'Stacy', 18, 'F', 540, 7271, 'BAL'),
    (1025, 'Goldman', 'Mark', 18, 'M', 520, 7134, 'PIT'),
    (1026, 'Pang', 'Eric', 19, 'M', 520, 7134, 'HKG'),
    (1027, 'Brody', 'Paul', 18, 'M', 520, 8723, 'LOS'),
    (1028, 'Rugh', 'Eric', 20, 'M', 550, 2311, 'ROC'),
    (1029, 'Han', 'Jun', 17, 'M', 100, 2311, 'PEK'),
    (1030, 'Cheng', 'Lisa', 21, 'F', 550, 2311, 'SFO'),
    (1031, 'Smith', 'Sarah', 20, 'F', 550, 8772, 'PHL'),
    (1032, 'Brown', 'Eric', 20, 'M', 550, 8772, 'ATL'),
    (1033, 'Simms', 'William', 18, 'M', 550, 8772, 'NAR'),
    (1034, 'Epp', 'Eric', 18, 'M', 50, 5718, 'BOS'),
    (1035, 'Schmidt', 'Sarah', 26, 'F', 50, 5718, 'WAS');

-- Has_Pet: 3 rows
INSERT INTO pets_1.Has_Pet (StuID, PetID) VALUES
    (1001, 2001),
    (1002, 2002),
    (1002, 2003);

-- Pets: 3 rows
INSERT INTO pets_1.Pets (PetID, PetType, pet_age, weight) VALUES
    (2001, 'cat', 3, 12.0),
    (2002, 'dog', 2, 13.4),
    (2003, 'dog', 1, 9.3);


-- Foreign key constraints (added after data load)
ALTER TABLE pets_1.Has_Pet
    ADD CONSTRAINT fk_Has_Pet_Student_0
    FOREIGN KEY (StuID)
    REFERENCES pets_1.Student (StuID);
ALTER TABLE pets_1.Has_Pet
    ADD CONSTRAINT fk_Has_Pet_Pets_1
    FOREIGN KEY (PetID)
    REFERENCES pets_1.Pets (PetID);
