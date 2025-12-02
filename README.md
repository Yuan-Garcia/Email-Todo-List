# Email-Todo-List

A Natural Language Processing project for classifying emails as business or casual, and generating prioritized to-do lists from email content.

## Project Overview

This project consists of two main components:

1. **Email Classification**: Classify emails as business (1) or casual (0)
2. **Todo List Generation**: LLM-based system to extract and prioritize tasks from emails

## Dataset

- **Enron Emails**: ~517k corporate emails (downloaded via Kaggle API)
- **Spam Assassin**: ~4.2k legitimate (ham) emails
- **Total**: ~521k emails after preprocessing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: Requires Python 3.10-3.11 (Python 3.13 has compatibility issues)

### 2. Setup Kaggle API (One-Time)

```bash
# Get credentials from https://www.kaggle.com/settings
# Click "Create New API Token" and download kaggle.json

mkdir -p ~/.kaggle
cp ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 3. Run Preprocessing Pipeline

```bash
cd src/preprocessing

# Test with 1000 emails (downloads from Kaggle automatically)
python preprocess_pipeline.py --test

# Full dataset
python preprocess_pipeline.py
```

The pipeline automatically downloads the Enron dataset from Kaggle if not found locally.

### 4. Explore the Data

```python
import pickle
import pandas as pd

# Load dictionary {email_text: label}
with open('../../Data/processed/email_label_dict.pkl', 'rb') as f:
    email_dict = pickle.load(f)

# Load metadata
metadata_df = pd.read_csv('../../Data/processed/metadata.csv')

print(f"Total emails: {len(email_dict)}")
```

### 5. Train Classifier (Optional)

```python
# Convert to lists
texts = list(email_dict.keys())
labels = list(email_dict.values())

# Split for training
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42, stratify=labels
)
```

## Output Format

The preprocessing pipeline creates:

```
Data/processed/
├── email_label_dict.pkl     # Dictionary {email_text: 0 or 1}
├── email_label_dict.json    # Sample (first 100 entries)
├── metadata.csv             # All metadata: from, to, subject, date, source, folder
└── statistics.txt           # Human-readable stats
```

### Dictionary Structure

```python
{
    "Subject: Meeting Tomorrow\n\nLet's meet at 3pm...": 1,  # business
    "Subject: Vacation Photos\n\nHere are the pics...": 0    # casual
}
```

- **Label 0** = Casual (personal emails)
- **Label 1** = Business (work emails)
- **email_text** = Subject + cleaned body (headers, quotes, signatures removed)

## Pipeline Features

### Email Cleaning
- Removes technical headers (Message-ID, X-*, routing info)
- Preserves subject in email_text
- Removes quoted replies and email signatures
- Normalizes whitespace

### Label Strategy

**Casual (0):**
- All Spam Assassin ham emails
- Enron folders: personal, family, church, vacation, fantasy, hobby, sports

**Business (1):**
- All other Enron emails: sent, inbox, meetings, projects, calendar, reports

### Kaggle Integration
- **Default**: Auto-downloads from Kaggle if local file missing
- **`--use-kaggle`**: Force download even if local file exists
- **`--no-kaggle`**: Disable Kaggle (fail if no local file)

## Command-Line Options

```bash
# Basic usage (auto-downloads if needed)
python preprocess_pipeline.py

# Test mode (1000 emails)
python preprocess_pipeline.py --test

# Limit Enron emails
python preprocess_pipeline.py --max-enron 50000

# Skip reprocessing (use cached temp files)
python preprocess_pipeline.py --skip-enron --skip-spam

# Force Kaggle download
python preprocess_pipeline.py --use-kaggle

# Disable Kaggle
python preprocess_pipeline.py --no-kaggle
```

## Project Structure

```
Email-Todo-List/
├── Data/                      # Auto-downloaded and processed data
│   ├── easy_ham/             # Spam Assassin dataset
│   ├── easy_ham_2/
│   ├── hard_ham/
│   └── processed/            # Pipeline output
├── src/
│   ├── preprocessing/        # Data preprocessing
│   │   ├── email_cleaner.py          # Text cleaning utilities
│   │   ├── process_enron.py          # Enron processor (Kaggle API)
│   │   ├── process_spam_assassin.py  # Spam Assassin processor
│   │   ├── build_dataset.py          # Dataset builder
│   │   └── preprocess_pipeline.py    # Main pipeline
│   ├── classifier/           # Model training
│   │   └── explore_emails_simple.py  # Data exploration script
│   └── todo_list/            # Todo generation
│       ├── call_LLM.py
│       └── generate_todo_list.py
├── requirements.txt
└── README.md
```

## Configuration

### Casual Folder Keywords

Edit in `src/preprocessing/process_enron.py`:

```python
CASUAL_KEYWORDS = [
    'personal', 'family', 'church', 'vacation', 'holiday', 'fantasy',
    'congratulations', 'birthday', 'wedding', 'baby', 'anniversary',
    'hobby', 'sport', 'game', 'social', 'friend', 'reunion', 'party',
    'entertainment', 'leisure', 'golf', 'tennis', 'football'
]
```

## Todo List Generation

```python
from src.todo_list.generate_todo_list import generate_todo_list

emails = ["Email content here...", "Another email..."]
todo_list = generate_todo_list(emails)
print(todo_list)
```

Features:
- Extracts explicit and implicit tasks
- Prioritizes by deadlines, sender authority, urgency
- Deduplicates similar tasks
- Structured output with metadata

## Troubleshooting

### Python Version Issues
- **Recommended**: Python 3.10 or 3.11
- **Issue**: Python 3.13 has pandas/numpy compatibility problems
- **Solution**: Use conda or pyenv

```bash
conda create -n email_proc python=3.11
conda activate email_proc
pip install -r requirements.txt
```

### Kaggle API Issues
```bash
# Verify kaggle.json is in the right place
ls -la ~/.kaggle/kaggle.json

# Should show: -rw------- (600 permissions)
# If not: chmod 600 ~/.kaggle/kaggle.json
```

### Memory Issues
- Process in smaller batches: `--max-enron 50000`
- Reduce batch sizes in training
- Use CPU instead of GPU

### Missing Local CSV
The pipeline automatically downloads from Kaggle if `Data/enron_emails.csv` is missing. Ensure Kaggle credentials are set up.

## Data Files in Git

The `.gitignore` excludes all files in `Data/*` to keep the repository clean. Each user downloads their own data via Kaggle.

## Expected Results

- **Total unique emails**: ~4,000-521k (depending on processing options)
- **Casual emails**: ~10% of dataset
- **Business emails**: ~90% of dataset
- **Average email length**: ~1,500 characters

## Citation

### Datasets
- **Enron Email Dataset**: [Kaggle - Enron Email Dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset)
- **Spam Assassin**: [Apache SpamAssassin Public Corpus](https://spamassassin.apache.org/old/publiccorpus/)

## License

MIT License - see LICENSE file for details

## Contributors

- Yuan Garcia (Original Project)
- CS159 Natural Language Processing Course

## Future Work

- [ ] Implement content-based classification
- [ ] Create web interface for todo list generation
- [ ] Integrate classification with todo generation
- [ ] Add multi-label classification (urgent/non-urgent)
- [ ] Implement active learning
