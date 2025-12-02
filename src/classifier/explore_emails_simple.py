"""
Simple script to explore the preprocessed email dataset.
Shows how to load and use the dictionary and metadata CSV.
"""

import pickle
import pandas as pd
import numpy as np
from collections import Counter


def main():
    """Load and explore the email dataset."""
    
    print("=" * 70)
    print("EMAIL DATASET EXPLORATION")
    print("=" * 70)
    
    # 1. Load dictionary
    print("\n1. Loading dictionary...")
    with open('../../Data/processed/email_label_dict.pkl', 'rb') as f:
        email_dict = pickle.load(f)
    
    print(f"   Loaded {len(email_dict):,} emails")
    
    # 2. Load metadata
    print("\n2. Loading metadata...")
    metadata_df = pd.read_csv('../../Data/processed/metadata.csv')
    print(f"   Loaded {len(metadata_df):,} metadata records")
    print(f"   Columns: {', '.join(metadata_df.columns)}")
    
    # 3. Basic statistics
    print("\n" + "=" * 70)
    print("DATASET STATISTICS")
    print("=" * 70)
    
    label_counts = Counter(email_dict.values())
    print(f"\nTotal unique emails: {len(email_dict):,}")
    
    print(f"\nLabel Distribution:")
    for label in sorted(label_counts.keys()):
        count = label_counts[label]
        pct = (count / len(email_dict)) * 100
        label_name = "casual" if label == 0 else "business"
        print(f"  {label} ({label_name:8s}): {count:,} ({pct:.1f}%)")
    
    # Email length statistics
    email_lengths = [len(text) for text in email_dict.keys()]
    print(f"\nEmail Length Statistics:")
    print(f"  Average:  {np.mean(email_lengths):,.0f} characters")
    print(f"  Median:   {np.median(email_lengths):,.0f} characters")
    print(f"  Min:      {np.min(email_lengths):,} characters")
    print(f"  Max:      {np.max(email_lengths):,} characters")
    
    # 4. Sample emails
    print("\n" + "=" * 70)
    print("SAMPLE EMAILS")
    print("=" * 70)
    
    # Get samples
    items = list(email_dict.items())
    casual_samples = [(text, label) for text, label in items if label == 0][:2]
    business_samples = [(text, label) for text, label in items if label == 1][:2]
    
    print("\n--- CASUAL EMAILS (label = 0) ---")
    for i, (text, label) in enumerate(casual_samples, 1):
        print(f"\nSample {i}:")
        print(text[:400])
        if len(text) > 400:
            print("...")
    
    print("\n--- BUSINESS EMAILS (label = 1) ---")
    for i, (text, label) in enumerate(business_samples, 1):
        print(f"\nSample {i}:")
        print(text[:400])
        if len(text) > 400:
            print("...")
    
    # 5. Metadata exploration
    print("\n" + "=" * 70)
    print("METADATA EXPLORATION")
    print("=" * 70)
    
    print(f"\nSource distribution:")
    print(metadata_df['source'].value_counts())
    
    print(f"\nLabel distribution in metadata:")
    print(metadata_df['label'].value_counts())
    
    # 6. Show how to use the data
    print("\n" + "=" * 70)
    print("HOW TO USE THE DATA")
    print("=" * 70)
    
    print("""
To use this data in your code:

1. Load the dictionary:
   import pickle
   with open('../../Data/processed/email_label_dict.pkl', 'rb') as f:
       email_dict = pickle.load(f)
   
2. Convert to lists for training:
   texts = list(email_dict.keys())
   labels = list(email_dict.values())
   
3. Split for training/testing:
   from sklearn.model_selection import train_test_split
   X_train, X_test, y_train, y_test = train_test_split(
       texts, labels, test_size=0.2, random_state=42, stratify=labels
   )

4. Access metadata for additional info:
   metadata_df = pd.read_csv('../../Data/processed/metadata.csv')
""")


if __name__ == "__main__":
    main()

