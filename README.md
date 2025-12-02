# Email-Todo-List

A Natural Language Processing project for classifying emails as business or casual, and generating prioritized to-do lists from email content.

## Project Overview

This project consists of two main components:

1. **Email Classification**: BERT-based model to classify emails as business or casual
2. **Todo List Generation**: LLM-based system to extract and prioritize tasks from emails

## Dataset

- **Enron Emails**: ~517k corporate emails with folder metadata
- **Spam Assassin**: ~4.2k legitimate (ham) emails
- **Total**: ~521k emails after preprocessing

## Project Structure

```
Email-Todo-List/
├── Data/                          # Dataset storage
│   ├── enron_emails.csv          # Enron dataset
│   ├── easy_ham/                 # Spam Assassin ham emails
│   ├── easy_ham_2/
│   ├── hard_ham/
│   └── processed/                # Preprocessed dataset output
│       ├── dataset/              # Hugging Face format
│       ├── statistics.json
│       └── label_distribution.txt
├── src/
│   ├── preprocessing/            # Dataset preprocessing pipeline
│   │   ├── email_cleaner.py
│   │   ├── process_enron.py
│   │   ├── process_spam_assassin.py
│   │   ├── build_dataset.py
│   │   ├── preprocess_pipeline.py
│   │   └── README.md
│   ├── classifier/               # BERT classification model
│   │   └── buisness_forecasting.ipynb
│   └── todo_list/                # Todo list generation
│       ├── call_LLM.py
│       └── generate_todo_list.py
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If using Python 3.13, you may encounter compatibility issues. We recommend Python 3.10-3.11.

### 2. Preprocess the Dataset

```bash
cd src/preprocessing

# Quick test with 1000 emails
python preprocess_pipeline.py --test

# Process full dataset
python preprocess_pipeline.py
```

See `src/preprocessing/README.md` for advanced options.

### 3. Train the Classifier

```bash
cd src/classifier
jupyter notebook buisness_forecasting.ipynb
```

The notebook is pre-configured to load the preprocessed dataset.

### 4. Generate Todo Lists

```python
from src.todo_list.generate_todo_list import generate_todo_list

emails = ["Email content here...", "Another email..."]
todo_list = generate_todo_list(emails)
print(todo_list)
```

## Features

### Email Preprocessing

- **Smart Cleaning**: Removes headers, quoted replies, signatures
- **Folder-Based Labeling**: Uses Enron folder metadata to classify emails
- **Balanced Datasets**: Handles class imbalance with undersampling/oversampling
- **Hugging Face Format**: Ready for transformer models

### Classification

- **Model**: BERT-base-uncased
- **Classes**: Business (0) vs Casual (1)
- **Features**:
  - Early stopping
  - Best model checkpointing
  - Comprehensive evaluation metrics

### Todo List Generation

- **Task Extraction**: Identifies explicit and implicit tasks
- **Prioritization**: Based on deadlines, sender authority, urgency
- **Deduplication**: Merges similar tasks across emails
- **Structured Output**: Formatted todo list with metadata

## Label Strategy

### Business Emails
- Enron folders: sent, inbox, meetings, projects, calendar, reports, etc.
- Corporate communications
- Work-related content

### Casual Emails
- Enron folders containing: personal, family, church, vacation, fantasy, hobby, sports
- Spam Assassin ham emails (legitimate personal emails)
- Personal communications

## Data Statistics

After preprocessing (with balancing):
- **Business emails**: 60-75% of dataset
- **Casual emails**: 25-40% of dataset
- **Train/Val/Test split**: 60/20/20

## Configuration

### Casual Folder Keywords

Edit in `src/preprocessing/process_enron.py`:
```python
CASUAL_KEYWORDS = [
    'personal', 'family', 'church', 'vacation', 'holiday', 'fantasy',
    'congratulations', 'birthday', 'wedding', 'baby', 'anniversary',
    # ... add more as needed
]
```

### Training Parameters

Edit in `src/classifier/buisness_forecasting.ipynb`:
```python
training_args = TrainingArguments(
    num_train_epochs=10,
    per_device_train_batch_size=16,
    learning_rate=3e-5,
    # ... adjust as needed
)
```

## Troubleshooting

### Python Version Issues
- **Recommended**: Python 3.10 or 3.11
- **Issue**: Python 3.13 may have pandas/numpy compatibility problems
- **Solution**: Use pyenv or conda to manage Python versions

### Memory Issues
- Reduce batch sizes in training
- Process dataset in chunks with `--max-enron` flag
- Use CPU instead of GPU if OOM errors occur

### Dataset Loading
If the dataset fails to load:
```bash
# Reprocess with smaller chunks
cd src/preprocessing
python preprocess_pipeline.py --max-enron 50000
```

## Development

### Adding New Data Sources

1. Create processor in `src/preprocessing/process_<source>.py`
2. Implement cleaning and labeling logic
3. Update `preprocess_pipeline.py` to include new source
4. Update `build_dataset.py` to handle new metadata

### Improving Classification

1. Adjust hyperparameters in notebook
2. Try different BERT variants (roberta, distilbert)
3. Add data augmentation
4. Experiment with different label strategies

## Performance

Expected results (after proper training):
- **Training Accuracy**: 70-85%
- **Validation Accuracy**: 65-75%
- **Test Accuracy**: 65-75%

Note: The original notebook showed overfitting (71% train → 49% val). The new preprocessing pipeline should improve generalization.

## Citation

### Datasets
- **Enron Email Dataset**: [Carnegie Mellon University](https://www.cs.cmu.edu/~./enron/)
- **Spam Assassin**: [Apache SpamAssassin Public Corpus](https://spamassassin.apache.org/old/publiccorpus/)

## License

MIT License - see LICENSE file for details

## Contributors

- Yuan Garcia (Original Project)
- CS159 Natural Language Processing Course

## Future Work

- [ ] Implement content-based classification (in addition to folder-based)
- [ ] Add more sophisticated balancing strategies
- [ ] Create web interface for todo list generation
- [ ] Integrate classification with todo generation
- [ ] Add multi-label classification (urgent/non-urgent, etc.)
- [ ] Implement active learning for better labeling
