#!/usr/bin/env python3
"""
Download and extract the Spider 1.0 dataset.

This script automates the process of:
1. Downloading the Spider dataset from Google Drive
2. Extracting it to the correct location
3. Verifying the dataset structure

Usage:
    python scripts/download_spider.py
"""

import os
import sys
import zipfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Spider 1.0 Dataset Download")
print("=" * 70)
print()

# Define paths
spider_dir = project_root / "data" / "spider"
zip_path = spider_dir / "spider-fixed.zip"
database_dir = spider_dir / "database"

# Create spider directory if it doesn't exist
spider_dir.mkdir(parents=True, exist_ok=True)

# Check if dataset already exists
if database_dir.exists() and any(database_dir.iterdir()):
    print("✅ Spider dataset appears to already be downloaded.")
    print(f"   Location: {database_dir}")
    print()
    response = input("Do you want to re-download? (y/N): ").strip().lower()
    if response != 'y':
        print("Skipping download.")
        sys.exit(0)

# Step 1: Download the dataset
print("[ 1/3 ] Downloading Spider dataset from Google Drive...")
print("         This may take a few minutes (104MB)...")
print()

try:
    import gdown
except ImportError:
    print("❌ gdown package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
    import gdown

# Google Drive file ID for Spider dataset
file_id = "1m68AHHPC4pqyjT-Zmt-u8TRqdw5vp-U5"

try:
    # Download to spider directory
    gdown.download(
        f"https://drive.google.com/uc?id={file_id}",
        str(zip_path),
        quiet=False
    )
    print()
    print(f"✅ Download complete: {zip_path}")
    print()
except Exception as e:
    print(f"❌ Download failed: {e}")
    print()
    print("You can manually download from:")
    print("https://drive.google.com/file/d/1m68AHHPC4pqyjT-Zmt-u8TRqdw5vp-U5/view")
    print(f"Save to: {zip_path}")
    sys.exit(1)

# Step 2: Extract the dataset
print("[ 2/3 ] Extracting dataset...")

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract to spider directory
        zip_ref.extractall(spider_dir)

    # Check if extracted to nested spider/spider/
    nested_spider = spider_dir / "spider"
    if nested_spider.exists() and nested_spider.is_dir():
        print("   Moving contents from nested directory...")
        # Move all contents up one level
        for item in nested_spider.iterdir():
            target = spider_dir / item.name
            if target.exists():
                print(f"   Warning: {item.name} already exists, skipping...")
                continue
            item.rename(target)
        # Remove empty nested directory
        nested_spider.rmdir()

    print("✅ Extraction complete")
    print()
except Exception as e:
    print(f"❌ Extraction failed: {e}")
    sys.exit(1)

# Step 3: Verify the dataset
print("[ 3/3 ] Verifying dataset structure...")

# Check for required files
required_files = [
    "README.txt",
    "dev.json",
    "train_spider.json",
    "train_others.json",
    "tables.json",
]

all_good = True
for filename in required_files:
    filepath = spider_dir / filename
    if filepath.exists():
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"   ✅ {filename:<25} ({size_mb:.1f} MB)")
    else:
        print(f"   ❌ {filename:<25} MISSING")
        all_good = False

# Check database directory
if database_dir.exists():
    db_count = len([d for d in database_dir.iterdir() if d.is_dir()])
    print(f"   ✅ {'database/':<25} ({db_count} databases)")

    if db_count != 166:
        print(f"   ⚠️  Expected 166 databases, found {db_count}")
        all_good = False
else:
    print(f"   ❌ {'database/':<25} MISSING")
    all_good = False

print()

if all_good:
    print("=" * 70)
    print("✅ Spider dataset successfully downloaded and verified!")
    print("=" * 70)
    print()
    print("Dataset location: data/spider/")
    print("Total databases: 166")
    print()
    print("Next steps:")
    print("  1. Select 15-20 databases for your project")
    print("  2. Convert SQLite databases to PostgreSQL")
    print("  3. Load into Supabase")
    print()
else:
    print("=" * 70)
    print("⚠️  Dataset verification found issues")
    print("=" * 70)
    print()
    print("Please check the error messages above and try again.")
    print("You can also manually download from:")
    print("https://drive.google.com/file/d/1m68AHHPC4pqyjT-Zmt-u8TRqdw5vp-U5/view")
    print()
    sys.exit(1)
