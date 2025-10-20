# Data Directory

This directory contains the Spider dataset and related data files.

## Structure

```
data/
├── spider/                 # Spider 1.0 dataset
│   ├── database/          # SQLite database files
│   ├── train_spider.json
│   ├── train_others.json
│   ├── dev.json           # Development/test questions
│   └── tables.json        # Schema metadata
├── spider-fixed/          # (Optional) Fixed version
└── scripts/               # Data processing scripts
```

## Download Spider Dataset

**Option 1: Direct download**
```bash
cd data
wget https://drive.google.com/uc?export=download&id=1TqleXec_OykOYFREKKtschzY29dUcVAQ -O spider.zip
unzip spider.zip
```

**Option 2: From GitHub**
```bash
git clone https://github.com/taoyds/spider.git
# Or the fixed version:
git clone https://github.com/CrafterKolyan/spider-fixed.git
```

## Selected Databases (15-20)

See `docs/project_plan.md` for the full list of selected databases:
- concert_singer
- pets_1
- flight_2
- car_1
- world_1
- student_transcripts_tracking
- employee_hire_evaluation
- cre_Doc_Template_Mgt
- course_teach
- museum_visit
- wta_1
- battle_death
- tvshow
- poker_player
- voter_1
- (and more...)

## Data Loading

The SQLite databases will be converted to PostgreSQL and loaded into Supabase using scripts in `scripts/` directory.

## .gitignore

Large database files are excluded from git. See `.gitignore`:
- `data/spider/*.sqlite`
- `data/spider/database/`
