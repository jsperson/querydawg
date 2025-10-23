-- Migration SQL for course_teach
-- Generated: 2025-10-22T12:09:49.751859
-- Source: /home/developer/source/dataprism/data/spider/database/course_teach/course_teach.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS course_teach;

-- Table: course
CREATE TABLE course_teach.course (
    Course_ID BIGINT,
    Staring_Date TEXT,
    Course TEXT,
    PRIMARY KEY (Course_ID)
);

-- Table: teacher
CREATE TABLE course_teach.teacher (
    Teacher_ID BIGINT,
    Name TEXT,
    Age TEXT,
    Hometown TEXT,
    PRIMARY KEY (Teacher_ID)
);

-- Table: course_arrange
CREATE TABLE course_teach.course_arrange (
    Course_ID BIGINT,
    Teacher_ID BIGINT,
    Grade BIGINT,
    PRIMARY KEY (Course_ID, Teacher_ID, Grade)
);

-- Data migration
-- course: 10 rows
INSERT INTO course_teach.course (Course_ID, Staring_Date, Course) VALUES
    (1, '5 May', 'Language Arts'),
    (2, '6 May', 'Math'),
    (3, '7 May', 'Science'),
    (4, '9 May', 'History'),
    (5, '10 May', 'Bible'),
    (6, '11 May', 'Geography'),
    (7, '13 May', 'Sports'),
    (8, '14 May', 'French'),
    (9, '15 May', 'Health'),
    (10, '17 May', 'Music');

-- teacher: 7 rows
INSERT INTO course_teach.teacher (Teacher_ID, Name, Age, Hometown) VALUES
    (1, 'Joseph Huts', '32', 'Blackrod Urban District'),
    (2, 'Gustaaf Deloor', '29', 'Bolton County Borough'),
    (3, 'Vicente Carretero', '26', 'Farnworth Municipal Borough'),
    (4, 'John Deloor', '33', 'Horwich Urban District'),
    (5, 'Kearsley Brown', '45', 'Kearsley Urban District'),
    (6, 'Anne Walker', '41', 'Little Lever Urban District'),
    (7, 'Lucy Wong', '39', 'Turton Urban District');

-- course_arrange: 6 rows
INSERT INTO course_teach.course_arrange (Course_ID, Teacher_ID, Grade) VALUES
    (2, 5, 1),
    (2, 3, 3),
    (3, 2, 5),
    (4, 6, 7),
    (5, 6, 1),
    (10, 7, 4);


-- Foreign key constraints (added after data load)
ALTER TABLE course_teach.course_arrange
    ADD CONSTRAINT fk_course_arrange_teacher_0
    FOREIGN KEY (Teacher_ID)
    REFERENCES course_teach.teacher (Teacher_ID);
ALTER TABLE course_teach.course_arrange
    ADD CONSTRAINT fk_course_arrange_course_1
    FOREIGN KEY (Course_ID)
    REFERENCES course_teach.course (Course_ID);
