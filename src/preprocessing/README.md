# Email Dataset Preprocessing Pipeline

This module preprocesses Enron and Spam Assassin email datasets for business/casual classification.

## Overview

The preprocessing pipeline:
1. Cleans email text (removes headers, quoted replies, signatures)
2. Labels emails as "business" or "casual" based on metadata
3. Balances the dataset
4. Splits into train/validation/test sets
5. Saves in Hugging Face Dataset format

## Files

- `email_cleaner.py` - Email text cleaning utilities
- `process_enron.py` - Enron dataset processor
- `process_spam_assassin.py` - Spam Assassin dataset processor
- `build_dataset.py` - Dataset combination and splitting
- `preprocess_pipeline.py` - Main pipeline script

## Setup

### 1. Install Dependencies

```bash
cd ../..
pip install -r requirements.txt
```

### 2. Prepare Data

Ensure you have the following data structure:
```
Data/
├── enron_emails.csv
├── easy_ham/
├── easy_ham_2/
└── hard_ham/
```

## Usage

### Quick Test (1000 Enron emails)

```bash
python preprocess_pipeline.py --test
```

### Process Full Dataset

```bash
python preprocess_pipeline.py
```

### Advanced Options

```bash
# Limit Enron emails
python preprocess_pipeline.py --max-enron 10000

# Change balancing strategy
python preprocess_pipeline.py --balance oversample

# Adjust class imbalance ratio
python preprocess_pipeline.py --balance undersample --max-ratio 2.0

# Skip steps (if already processed)
python preprocess_pipeline.py --skip-enron --skip-spam
```

## Output

The pipeline creates:

```
Data/processed/
├── dataset/              # Hugging Face Dataset
│   ├── train/
│   ├── validation/
│   └── test/
├── statistics.json       # Dataset statistics
└── label_distribution.txt # Readable statistics
```

## Label Strategy

### Enron Emails
- **Casual**: Folders containing keywords like "personal", "family", "church", "vacation", "fantasy", etc.
- **Business**: All other folders (default for corporate environment)

### Spam Assassin
- **Casual**: All ham (legitimate) emails labeled as casual/personal

## Configuration

Edit the following in the scripts:

**Casual Keywords** (`process_enron.py`):
```python
CASUAL_KEYWORDS = [
    'personal', 'family', 'church', 'vacation', 'holiday', 'fantasy',
    'congratulations', 'birthday', 'wedding', 'baby', 'anniversary',
    'hobby', 'sport', 'game', 'social', 'friend', 'reunion', 'party',
    'entertainment', 'leisure', 'hobby', 'golf', 'tennis', 'football',
    'baseball', 'soccer', 'recreation', 'club'
]
```

**Split Ratios** (`build_dataset.py`):
```python
create_train_val_test_split(df, train=0.6, val=0.2, test=0.2)
```

## Individual Module Testing

Test each module independently:

```bash
# Test email cleaner
python email_cleaner.py

# Test Enron processor
python process_enron.py

# Test Spam Assassin processor  
python process_spam_assassin.py

# Test dataset builder
python build_dataset.py
```

## Expected Output

### Dataset Size
- **Total**: ~521k emails
- **Business**: ~450-480k emails (most Enron emails)
- **Casual**: ~40-70k emails (Spam Assassin + Enron personal folders)

### Dataset Statistics
After running, check:
- `Data/processed/statistics.json` - Complete statistics
- `Data/processed/label_distribution.txt` - Human-readable summary

### Loading the Dataset

In Python:
```python
from datasets import load_from_disk

dataset = load_from_disk('../../Data/processed/dataset')

# Access splits
train = dataset['train']
val = dataset['validation']
test = dataset['test']

# Examine a sample
print(train[0])
# {'email_text': 'Subject: ...\n\n...', 'label': 'business', 'source': 'enron', ...}
```

## Troubleshooting

### Python Version Issues
If you encounter segmentation faults with Python 3.13, try using Python 3.10-3.11 instead.

### Memory Issues
- Reduce batch processing size in the code
- Process Enron emails in chunks with `--max-enron`
- Use the `--skip-enron` or `--skip-spam` flags to process incrementally

### CSV Field Size Error
The code automatically increases the CSV field size limit. If you still encounter errors, increase it further in `process_enron.py`:
```python
csv.field_size_limit(20000000)  # Increase as needed
```

## Next Steps

After preprocessing, use the dataset with the BERT classifier:

```bash
cd ../classifier
jupyter notebook buisness_forecasting.ipynb
```

The notebook is already configured to load from `../../Data/processed/dataset`.

