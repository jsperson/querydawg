-- Migration SQL for tvshow
-- Generated: 2025-10-20T20:18:43.303302
-- Source: /home/developer/source/dataprism/data/spider/database/tvshow/tvshow.sqlite

-- Create schema
CREATE SCHEMA IF NOT EXISTS tvshow;

-- Table: TV_Channel
CREATE TABLE tvshow.TV_Channel (
    id TEXT,
    series_name TEXT,
    Country TEXT,
    Language TEXT,
    Content TEXT,
    Pixel_aspect_ratio_PAR TEXT,
    Hight_definition_TV TEXT,
    Pay_per_view_PPV TEXT,
    Package_Option TEXT,
    PRIMARY KEY (id)
);

-- Table: TV_series
CREATE TABLE tvshow.TV_series (
    id DOUBLE PRECISION,
    Episode TEXT,
    Air_Date TEXT,
    Rating TEXT,
    Share DOUBLE PRECISION,
    "18_49_Rating_Share" TEXT,
    Viewers_m TEXT,
    Weekly_Rank DOUBLE PRECISION,
    Channel TEXT,
    PRIMARY KEY (id)
);

-- Table: Cartoon
CREATE TABLE tvshow.Cartoon (
    id DOUBLE PRECISION,
    Title TEXT,
    Directed_by TEXT,
    Written_by TEXT,
    Original_air_date TEXT,
    Production_code DOUBLE PRECISION,
    Channel TEXT,
    PRIMARY KEY (id)
);

-- Data migration
-- TV_Channel: 15 rows
INSERT INTO tvshow.TV_Channel (id, series_name, Country, Language, Content, Pixel_aspect_ratio_PAR, Hight_definition_TV, Pay_per_view_PPV, Package_Option) VALUES
    ('700', 'Sky Radio', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'Sky Famiglia'),
    ('701', 'Sky Music', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'Sky Famiglia'),
    ('703', 'Music Box Italia', 'Italy', 'Italian', 'music', '4:3 / 16:9', 'no', 'no', 'Sky Famiglia'),
    ('704', 'MTV Hits', 'Italy', 'Italian', 'music', '16:9', 'no', 'no', 'Sky Famiglia'),
    ('705', 'MTV Classic', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'Sky Famiglia'),
    ('706', 'MTV Rocks', 'United Kingdom', 'English', 'music', '16:9', 'no', 'no', 'Sky Famiglia'),
    ('707', 'MTV Dance', 'United Kingdom', 'English', 'music', '16:9', 'no', 'no', 'Sky Famiglia'),
    ('708', 'MTV Music', 'Italy', 'Italian', 'music', '16:9', 'no', 'no', 'no ( FTV )'),
    ('709', 'MTV Live HD', 'Poland', 'English', 'music', '16:9', 'yes', 'no', 'Sky Famiglia + Sky HD'),
    ('713', 'Radio Capital TiVù', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'no ( FTV )'),
    ('714', 'myDeejay', 'Italy', 'Italian', 'music', '16:9', 'no', 'no', 'Sky Famiglia'),
    ('715', 'Match Music', 'Italy', 'Italian', 'music', '4:3 / 16:9', 'no', 'no', 'Sky Famiglia'),
    ('717', 'Rock TV', 'Italy', 'Italian', 'music', '4:3 / 16:9', 'no', 'no', 'Sky Famiglia'),
    ('719', 'Hip Hop TV', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'Sky Famiglia'),
    ('728', 'Classica', 'Italy', 'Italian', 'music', '4:3', 'no', 'no', 'Option');

-- TV_series: 12 rows
INSERT INTO tvshow.TV_series (id, Episode, Air_Date, Rating, Share, "18_49_Rating_Share", Viewers_m, Weekly_Rank, Channel) VALUES
    (1.0, 'A Love of a Lifetime', 'September 24, 2007', '5.8', 9.0, '3.5/9', '9.16', 43.0, '700'),
    (2.0, 'Friendly Skies', 'October 1, 2007', '5.3', 9.0, '3.2/8', '8.23', 50.0, '701'),
    (3.0, 'Game Three', 'October 8, 2007', '4.4', 7.0, '2.9/7', '6.94', 61.0, '707'),
    (4.0, 'The Year of the Rabbit', 'October 15, 2007', '4.3', 7.0, '2.7/7', '6.75', 67.0, '713'),
    (5.0, 'The Legend of Dylan McCleen', 'October 22, 2007', '3.8', 6.0, '2.4/6', '6.06', 72.0, '714'),
    (6.0, 'Keepers', 'October 29, 2007', '3.7', 6.0, '2.2/6', '5.75', 71.0, '700'),
    (7.0, 'Double Down', 'November 5, 2007', '3.4', 6.0, '2.1/5', '5.13', 80.0, '708'),
    (8.0, 'Winterland', 'November 12, 2007', '4.0', 7.0, '2.4/6', '6.09', 70.0, '707'),
    (9.0, 'Emily', 'November 19, 2007', '3.7', 6.0, '2.2/6', '5.61', 66.0, '717'),
    (10.0, 'Blowback', 'November 26, 2007', '3.7', 6.0, '2.4/6', '6.05', 68.0, '719'),
    (11.0, 'Home By Another Way', 'December 10, 2007', '3.5', 6.0, '1.7/5', '5.28', 62.0, '728'),
    (12.0, 'The Hanged Man', 'December 17, 2007', '3.0', 5.0, '1.5/4', '4.24', 65.0, '714');

-- Cartoon: 12 rows
INSERT INTO tvshow.Cartoon (id, Title, Directed_by, Written_by, Original_air_date, Production_code, Channel) VALUES
    (1.0, 'The Rise of the Blue Beetle!', 'Ben Jones', 'Michael Jelenic', 'November14,2008', 101.0, '700'),
    (2.0, 'Terror on Dinosaur Island!', 'Brandon Vietti', 'Steven Melching', 'November21,2008', 102.0, '701'),
    (3.0, 'Evil Under the Sea!', 'Michael Chang', 'Joseph Kuhr', 'December5,2008', 103.0, '703'),
    (4.0, 'Day of the Dark Knight!', 'Ben Jones', 'J. M. DeMatteis', 'January2,2009', 104.0, '704'),
    (5.0, 'Invasion of the Secret Santas!', 'Brandon Vietti', 'Adam Beechen', 'December12,2008', 105.0, '705'),
    (6.0, 'Enter the Outsiders!', 'Michael Chang', 'Todd Casey', 'January9,2009', 106.0, '706'),
    (7.0, 'Dawn of the Dead Man!', 'Ben Jones', 'Steven Melching', 'January16,2009', 107.0, '707'),
    (8.0, 'Fall of the Blue Beetle!', 'Brandon Vietti', 'James Krieg', 'January23,2009', 108.0, '708'),
    (9.0, 'Journey to the Center of the Bat!', 'Michael Chang', 'Matt Wayne', 'January30,2009', 109.0, '707'),
    (10.0, 'The Eyes of Despero!', 'Ben Jones', 'J. M. DeMatteis', 'February6,2009', 110.0, '728'),
    (11.0, 'Return of the Fearsome Fangs!', 'Brandon Vietti', 'Todd Casey', 'February20,2009', 111.0, '700'),
    (12.0, 'Deep Cover for Batman!', 'Michael Chang', 'Joseph Kuhr', 'February27,2009', 112.0, '707');


-- Foreign key constraints (added after data load)
ALTER TABLE tvshow.TV_series
    ADD CONSTRAINT fk_TV_series_TV_Channel_0
    FOREIGN KEY (Channel)
    REFERENCES tvshow.TV_Channel (id);
ALTER TABLE tvshow.Cartoon
    ADD CONSTRAINT fk_Cartoon_TV_Channel_0
    FOREIGN KEY (Channel)
    REFERENCES tvshow.TV_Channel (id);
