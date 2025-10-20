# Spider Dataset Download Instructions

The Spider 1.0 dataset is **not included** in this repository due to its size (~140MB extracted, 104MB compressed). Follow these instructions to download and set up the dataset locally.

## Quick Setup (Automated)

From the project root, run:

```bash
# Activate virtual environment
source venv/bin/activate

# Run download script
python scripts/download_spider.py
```

This will:
1. Download the Spider dataset from Google Drive (104MB)
2. Extract it to `data/spider/`
3. Verify the dataset structure

## Manual Setup

If you prefer to download manually:

### 1. Download the Dataset

Download from one of these sources:
- **Google Drive (recommended)**: https://drive.google.com/file/d/1m68AHHPC4pqyjT-Zmt-u8TRqdw5vp-U5/view
- **Official Spider GitHub**: https://github.com/taoyds/spider

### 2. Extract to Correct Location

```bash
# If you downloaded spider-fixed.zip, extract it:
cd data/spider/
unzip spider-fixed.zip

# Move contents up if nested:
mv spider/* .
rmdir spider
```

### 3. Verify Structure

Your `data/spider/` directory should look like this:

```
data/spider/
├── README.txt              # Dataset documentation
├── database/              # 166 SQLite databases
│   ├── academic/
│   ├── aircraft/
│   ├── car_1/
│   └── ... (163 more)
├── dev.json               # 1,034 dev/test examples
├── dev_gold.sql          # Gold standard SQL
├── tables.json           # Schema metadata for all databases
├── train_gold.sql        # Training gold standard SQL
├── train_others.json     # 1,659 training examples (6 databases)
└── train_spider.json     # 7,000 training examples (140 databases)
```

### 4. Verify Installation

Run the verification script:

```bash
python scripts/verify_spider.py
```

This will check:
- ✅ All required files exist
- ✅ Database count is correct (166)
- ✅ JSON files are valid
- ✅ Sample database can be opened

## Dataset Information

**Spider 1.0** is a large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL tasks.

- **166 databases** across various domains
- **8,659 training examples** (7,000 from Spider + 1,659 from other sources)
- **1,034 dev/test examples** across 20 databases
- **SQLite format** (will be converted to PostgreSQL for this project)

### Citation

If you use the Spider dataset, please cite:

```bibtex
@inproceedings{Yu&al.18c,
  year =         2018,
  title =        {Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task},
  booktitle =    {EMNLP},
  author =       {Tao Yu and Rui Zhang and Kai Yang and Michihiro Yasunaga and Dongxu Wang and Zifan Li and James Ma and Irene Li and Qingning Yao and Shanelle Roman and Zilin Zhang and Dragomir Radev}
}
```

## Troubleshooting

### Download fails
- Check your internet connection
- Verify the Google Drive link is still active
- Try the official Spider GitHub repository as alternative source

### Wrong directory structure
- Make sure you're extracting to `data/spider/`, not `data/`
- If you get nested `spider/spider/`, move contents up one level

### Permission errors
- Make sure you have write permissions to the `data/spider/` directory
- On Unix systems, you may need to make the download script executable: `chmod +x scripts/download_spider.py`

## Links

- **Official Spider Website**: https://yale-lily.github.io/spider
- **Spider GitHub**: https://github.com/taoyds/spider
- **Paper**: https://arxiv.org/abs/1809.08887
- **Leaderboard**: https://yale-lily.github.io/spider

## File Sizes

- `spider-fixed.zip`: ~104MB
- Extracted total: ~140MB
- `database/`: ~37MB (166 SQLite files)
- `train_spider.json`: ~24MB
- `train_others.json`: ~7.6MB
- `dev.json`: ~3.6MB
