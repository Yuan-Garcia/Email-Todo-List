"""
Spam Assassin ham email processor.
Processes legitimate emails from Spam Assassin dataset, labeling them as casual.
"""

import os
import pandas as pd
from typing import List
from tqdm import tqdm
from email_cleaner import clean_email_text


def read_email_file(file_path: str) -> str:
    """
    Read raw email content from file.
    
    Args:
        file_path: Path to email file
        
    Returns:
        Raw email text
    """
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        # Fallback to latin-1
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""


def get_email_files_from_directory(directory: str) -> List[tuple]:
    """
    Get all email files from a directory.
    
    Args:
        directory: Path to directory containing email files
        
    Returns:
        List of tuples (file_path, file_name)
    """
    email_files = []
    
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist")
        return email_files
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories and hidden files
        if os.path.isfile(file_path) and not filename.startswith('.'):
            email_files.append((file_path, filename))
    
    return email_files


def combine_ham_folders(easy_ham_dir: str, easy_ham2_dir: str, hard_ham_dir: str) -> List[tuple]:
    """
    Combine email files from all three ham folders.
    
    Args:
        easy_ham_dir: Path to easy_ham directory
        easy_ham2_dir: Path to easy_ham_2 directory
        hard_ham_dir: Path to hard_ham directory
        
    Returns:
        List of tuples (file_path, file_name, difficulty)
    """
    all_emails = []
    
    print("Collecting email files from Spam Assassin directories...")
    
    # Easy ham
    easy_ham_files = get_email_files_from_directory(easy_ham_dir)
    for file_path, filename in easy_ham_files:
        all_emails.append((file_path, filename, 'easy'))
    print(f"Found {len(easy_ham_files)} files in easy_ham")
    
    # Easy ham 2
    easy_ham2_files = get_email_files_from_directory(easy_ham2_dir)
    for file_path, filename in easy_ham2_files:
        all_emails.append((file_path, filename, 'easy'))
    print(f"Found {len(easy_ham2_files)} files in easy_ham_2")
    
    # Hard ham
    hard_ham_files = get_email_files_from_directory(hard_ham_dir)
    for file_path, filename in hard_ham_files:
        all_emails.append((file_path, filename, 'hard'))
    print(f"Found {len(hard_ham_files)} files in hard_ham")
    
    print(f"Total: {len(all_emails)} email files")
    
    return all_emails


def process_spam_assassin_dataset(data_dir: str, output_path: str = None) -> pd.DataFrame:
    """
    Process Spam Assassin ham emails, labeling all as casual.
    
    Args:
        data_dir: Base directory containing easy_ham, easy_ham_2, hard_ham folders
        output_path: Optional path to save intermediate results
        
    Returns:
        DataFrame with processed emails
    """
    # Construct paths
    easy_ham_dir = os.path.join(data_dir, 'easy_ham')
    easy_ham2_dir = os.path.join(data_dir, 'easy_ham_2')
    hard_ham_dir = os.path.join(data_dir, 'hard_ham')
    
    # Collect all email files
    all_emails = combine_ham_folders(easy_ham_dir, easy_ham2_dir, hard_ham_dir)
    
    processed_emails = []
    errors = 0
    
    print("\nProcessing Spam Assassin emails...")
    for file_path, filename, difficulty in tqdm(all_emails, desc="Processing Spam Assassin"):
        try:
            # Read email
            raw_email = read_email_file(file_path)
            
            if not raw_email or len(raw_email.strip()) < 10:
                continue
            
            # Clean email
            cleaned = clean_email_text(raw_email)
            
            # Skip if email text is too short
            if len(cleaned['email_text'].strip()) < 10:
                continue
            
            # Create processed record
            # All Spam Assassin ham emails are labeled as casual
            processed_emails.append({
                'email_text': cleaned['email_text'],
                'label': 'casual',
                'source': 'spam_assassin',
                'difficulty': difficulty,
                'filename': filename,
                'from': cleaned['from'],
                'to': cleaned['to'],
                'subject': cleaned['subject'],
                'date': cleaned['date']
            })
            
        except Exception as e:
            errors += 1
            if errors <= 10:  # Print first 10 errors
                print(f"Error processing {filename}: {str(e)[:100]}")
            continue
    
    print(f"\nProcessed {len(processed_emails)} emails successfully")
    print(f"Encountered {errors} errors")
    
    # Create DataFrame
    result_df = pd.DataFrame(processed_emails)
    
    # Print statistics
    print("\nDifficulty distribution:")
    print(result_df['difficulty'].value_counts())
    
    # Save if output path specified
    if output_path:
        print(f"\nSaving to {output_path}...")
        result_df.to_pickle(output_path)
        print("Saved!")
    
    return result_df


if __name__ == "__main__":
    # Test processor
    import os
    
    # Get absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'Data')
    output_path = os.path.join(base_dir, 'Data', 'temp_spam_test.pkl')
    
    print(f"Testing Spam Assassin processor...")
    print(f"Data directory: {data_dir}")
    
    df = process_spam_assassin_dataset(data_dir, output_path)
    
    print(f"\nSample processed email:")
    print(df.iloc[0]['email_text'][:500])

