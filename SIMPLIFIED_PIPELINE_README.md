# Simplified Email Preprocessing Pipeline

## Overview

The pipeline has been simplified to output two files:
1. **Dictionary** (`email_label_dict.pkl`): `{email_text: label}` where label is 0 (casual) or 1 (business)
2. **Metadata CSV** (`metadata.csv`): All email metadata in a separate file

## What Changed

### ✅ Kept (No Changes)
- `email_cleaner.py` - All cleaning functions (includes subject in email_text)
- `process_enron.py` - Enron email processor
- `process_spam_assassin.py` - Spam Assassin processor

### ✏️ Modified
- `build_dataset.py` - Removed HuggingFace Dataset code, train/val/test splitting, balancing
- `preprocess_pipeline.py` - Simplified to output dictionary and CSV

### ➕ Added
- `explore_emails_simple.py` - Simple script to load and explore the data

## Output Files

After running the pipeline, you'll find:

```
Data/processed/
├── email_label_dict.pkl     # Main dictionary {email_text: 0 or 1}
├── email_label_dict.json    # Sample (first 100 entries) for inspection
├── metadata.csv             # All metadata: from, to, subject, date, source, folder, etc.
└── statistics.txt           # Human-readable stats
```

## How to Run

### Option 1: Full Pipeline
```bash
cd src/preprocessing

# Process all emails (may take a while)
python preprocess_pipeline.py

# Or test with limited emails
python preprocess_pipeline.py --test  # Only 1000 Enron emails
```

### Option 2: Use Existing Temp Files
```bash
# If you already processed Enron/Spam Assassin
python preprocess_pipeline.py --skip-enron --skip-spam
```

## How to Use the Output

### Load the Dictionary

```python
import pickle

# Load dictionary
with open('Data/processed/email_label_dict.pkl', 'rb') as f:
    email_dict = pickle.load(f)

# email_dict structure:
# {
#     "Subject: Meeting Tomorrow\n\nLet's meet at 3pm...": 1,  # business
#     "Subject: Vacation Photos\n\nHere are the pics...": 0    # casual
# }

print(f"Total emails: {len(email_dict)}")
```

### Load the Metadata

```python
import pandas as pd

metadata_df = pd.read_csv('Data/processed/metadata.csv')

# Columns: email_text, label, source, from, to, subject, date, 
#          user_id, folder_name, difficulty, filename
```

### Convert for Training

```python
# Convert to lists
texts = list(email_dict.keys())   # Email texts (with subjects)
labels = list(email_dict.values()) # 0 (casual) or 1 (business)

# Split for training
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, 
    test_size=0.2, 
    random_state=42, 
    stratify=labels
)
```

### Explore the Data

```bash
# Run the exploration script
cd src/classifier
python explore_emails_simple.py
```

## Label Encoding

- **0** = Casual (personal, informal emails)
  - All Spam Assassin ham emails
  - Enron emails from folders: personal, family, church, vacation, fantasy, etc.

- **1** = Business (professional, work-related emails)
  - All other Enron emails (sent, inbox, meetings, projects, etc.)

## Email Text Format

Each email text includes the subject line:
```
Subject: Your Subject Here

Email body content...
```

This ensures you don't lose important information from the subject.

## Statistics

After running, check:
- `Data/processed/statistics.txt` - Human-readable summary
- `Data/processed/statistics.json` - Machine-readable stats

Expected dataset size (full run):
- Total: ~521k emails
- Business: ~450-480k (90%+)
- Casual: ~40-70k (10%)

## Troubleshooting

### Python 3.13 Issues
If you get segmentation faults, try using Python 3.10 or 3.11:
```bash
conda create -n email_proc python=3.11
conda activate email_proc
pip install -r requirements.txt
```

### Memory Issues
Process in smaller batches:
```bash
python preprocess_pipeline.py --max-enron 50000
```

### Checking Output
```python
# Quick check if files exist
import os
print("Dictionary exists:", os.path.exists('Data/processed/email_label_dict.pkl'))
print("Metadata exists:", os.path.exists('Data/processed/metadata.csv'))

# Check file sizes
import os
dict_size = os.path.getsize('Data/processed/email_label_dict.pkl') / (1024**2)
csv_size = os.path.getsize('Data/processed/metadata.csv') / (1024**2)
print(f"Dictionary: {dict_size:.1f} MB")
print(f"Metadata: {csv_size:.1f} MB")
```

## Next Steps

1. Run the pipeline to generate the files
2. Use `explore_emails_simple.py` to verify the data
3. Load the dictionary in your model training code
4. Split the data as needed for your specific use case
5. Train your classifier!

## Benefits of This Approach

✅ **Simple**: Just a dictionary and CSV - no complex formats  
✅ **Flexible**: Split data however you want for your use case  
✅ **Fast**: Quick to load and use  
✅ **Portable**: Easy to share and use in different environments  
✅ **Complete**: All metadata preserved separately  
✅ **Clean**: Subjects included, proper email cleaning applied

