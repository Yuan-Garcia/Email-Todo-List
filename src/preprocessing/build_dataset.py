"""
Simplified dataset builder for combining and saving email datasets.
Creates a simple dictionary {email_text: label} and metadata CSV.
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from typing import Dict


def combine_datasets(enron_df: pd.DataFrame, spam_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine Enron and Spam Assassin datasets.
    
    Args:
        enron_df: Processed Enron emails DataFrame
        spam_df: Processed Spam Assassin emails DataFrame
        
    Returns:
        Combined DataFrame
    """
    print("Combining datasets...")
    
    # Ensure both have the same required columns
    required_cols = ['email_text', 'label', 'source']
    
    for col in required_cols:
        if col not in enron_df.columns or col not in spam_df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Combine
    combined_df = pd.concat([enron_df, spam_df], ignore_index=True)
    
    print(f"Combined dataset size: {len(combined_df)} emails")
    print(f"  - From Enron: {len(enron_df)}")
    print(f"  - From Spam Assassin: {len(spam_df)}")
    
    return combined_df


def create_text_label_dict(df: pd.DataFrame) -> Dict[str, int]:
    """
    Create a dictionary mapping email_text to label (0 or 1).
    
    Args:
        df: DataFrame with 'email_text' and 'label' columns
        
    Returns:
        Dictionary {email_text: label}
    """
    print("\nCreating text-label dictionary...")
    
    # Create dictionary
    text_label_dict = {}
    duplicates = 0
    
    for idx, row in df.iterrows():
        email_text = row['email_text']
        label = row['label']
        
        # Handle duplicates (keep first occurrence)
        if email_text in text_label_dict:
            duplicates += 1
        else:
            text_label_dict[email_text] = label
    
    if duplicates > 0:
        print(f"  Warning: Found {duplicates} duplicate email texts (kept first occurrence)")
    
    print(f"  Dictionary size: {len(text_label_dict)} unique emails")
    
    return text_label_dict


def save_dict_as_pickle(data_dict: Dict, output_path: str):
    """
    Save dictionary as pickle file.
    
    Args:
        data_dict: Dictionary to save
        output_path: Output file path
    """
    print(f"\nSaving dictionary as pickle to {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(data_dict, f)
    
    print(f"  Saved {len(data_dict)} entries")


def save_dict_as_json(data_dict: Dict, output_path: str, sample_only: bool = True):
    """
    Save dictionary as JSON file.
    
    Args:
        data_dict: Dictionary to save
        output_path: Output file path
        sample_only: If True, only save first 100 entries (for readability)
    """
    print(f"\nSaving dictionary as JSON to {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if sample_only and len(data_dict) > 100:
        # Save only first 100 for readability
        items = list(data_dict.items())[:100]
        save_dict = dict(items)
        print(f"  Saving first 100 entries as sample (full data in pickle)")
    else:
        save_dict = data_dict
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_dict, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved {len(save_dict)} entries")


def save_metadata_csv(df: pd.DataFrame, output_path: str):
    """
    Save all metadata to CSV file.
    
    Args:
        df: DataFrame with all columns
        output_path: Output CSV path
    """
    print(f"\nSaving metadata to {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save all columns
    df.to_csv(output_path, index=False)
    
    print(f"  Saved {len(df)} rows with {len(df.columns)} columns")
    print(f"  Columns: {', '.join(df.columns)}")


def generate_dataset_statistics(df: pd.DataFrame, output_dir: str):
    """
    Generate and save dataset statistics.
    
    Args:
        df: Combined DataFrame
        output_dir: Output directory for statistics files
    """
    print("\nGenerating dataset statistics...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute statistics
    stats = {
        'total_emails': len(df),
        'unique_emails': df['email_text'].nunique(),
        'label_distribution': df['label'].value_counts().to_dict(),
        'source_distribution': df['source'].value_counts().to_dict(),
        'avg_email_length': float(df['email_text'].str.len().mean()),
        'median_email_length': float(df['email_text'].str.len().median()),
        'min_email_length': int(df['email_text'].str.len().min()),
        'max_email_length': int(df['email_text'].str.len().max())
    }
    
    # Add Enron folder distribution if available
    if 'folder_name' in df.columns:
        enron_df = df[df['source'] == 'enron']
        if len(enron_df) > 0:
            folder_counts = enron_df['folder_name'].value_counts().head(30).to_dict()
            stats['top_enron_folders'] = folder_counts
    
    # Add Spam Assassin difficulty distribution if available
    if 'difficulty' in df.columns:
        spam_df = df[df['source'] == 'spam_assassin']
        if len(spam_df) > 0:
            difficulty_counts = spam_df['difficulty'].value_counts().to_dict()
            stats['spam_assassin_difficulty'] = difficulty_counts
    
    # Save statistics as JSON
    stats_path = os.path.join(output_dir, 'statistics.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved statistics to {stats_path}")
    
    # Save label distribution as text
    stats_text_path = os.path.join(output_dir, 'statistics.txt')
    with open(stats_text_path, 'w') as f:
        f.write("Dataset Statistics\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total emails: {stats['total_emails']}\n")
        f.write(f"Unique emails: {stats['unique_emails']}\n\n")
        
        f.write("Label Distribution:\n")
        for label, count in sorted(stats['label_distribution'].items()):
            pct = count / stats['total_emails'] * 100
            label_name = "casual" if label == 0 else "business"
            f.write(f"  {label} ({label_name}): {count} ({pct:.1f}%)\n")
        
        f.write("\nSource Distribution:\n")
        for source, count in stats['source_distribution'].items():
            pct = count / stats['total_emails'] * 100
            f.write(f"  {source}: {count} ({pct:.1f}%)\n")
        
        f.write("\nEmail Length Statistics:\n")
        f.write(f"  Average: {stats['avg_email_length']:.0f} characters\n")
        f.write(f"  Median: {stats['median_email_length']:.0f} characters\n")
        f.write(f"  Min: {stats['min_email_length']} characters\n")
        f.write(f"  Max: {stats['max_email_length']} characters\n")
        
        if 'top_enron_folders' in stats:
            f.write("\nTop 30 Enron Folders:\n")
            for folder, count in stats['top_enron_folders'].items():
                f.write(f"  {folder}: {count}\n")
        
        if 'spam_assassin_difficulty' in stats:
            f.write("\nSpam Assassin Difficulty Distribution:\n")
            for diff, count in stats['spam_assassin_difficulty'].items():
                f.write(f"  {diff}: {count}\n")
    
    print(f"Saved text statistics to {stats_text_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    print(f"Total emails: {stats['total_emails']}")
    print(f"Unique emails: {stats['unique_emails']}")
    print(f"\nLabel distribution:")
    for label, count in sorted(stats['label_distribution'].items()):
        pct = count / stats['total_emails'] * 100
        label_name = "casual" if label == 0 else "business"
        print(f"  {label} ({label_name}): {count} ({pct:.1f}%)")
    print(f"\nAverage email length: {stats['avg_email_length']:.0f} characters")
    print("=" * 50)


if __name__ == "__main__":
    # Test with sample data
    print("Testing simplified dataset builder...")
    
    # Create sample data
    sample_enron = pd.DataFrame({
        'email_text': ['Subject: Meeting\n\nBusiness email 1', 'Subject: Report\n\nBusiness email 2'] * 50,
        'label': ['business'] * 100,
        'source': ['enron'] * 100,
        'folder_name': ['sent'] * 100
    })
    
    sample_spam = pd.DataFrame({
        'email_text': ['Subject: Hello\n\nCasual email 1', 'Subject: Party\n\nCasual email 2'] * 10,
        'label': ['casual'] * 20,
        'source': ['spam_assassin'] * 20,
        'difficulty': ['easy'] * 20
    })
    
    # Combine
    combined = combine_datasets(sample_enron, sample_spam)
    
    # Encode labels
    combined['label'] = combined['label'].map({'casual': 0, 'business': 1})
    
    # Create dictionary
    text_dict = create_text_label_dict(combined)
    
    print(f"\nSample entries from dictionary:")
    for i, (text, label) in enumerate(list(text_dict.items())[:2]):
        print(f"{i+1}. Label {label}: {text[:50]}...")
