"""
Enron email dataset processor.
Loads, cleans, and labels Enron emails based on folder metadata.
Uses Kaggle API to download dataset if not available locally.
"""

import csv
import pandas as pd
import sys
import os
import zipfile
from typing import Dict, List
from tqdm import tqdm
from email_cleaner import clean_email_text

try:
    import kagglehub
    KAGGLE_AVAILABLE = True
except ImportError:
    KAGGLE_AVAILABLE = False
    print("Warning: kagglehub not installed. Install with: pip install kagglehub")


# Increase CSV field size limit for large email content
csv.field_size_limit(10000000)


# Casual folder keywords (case-insensitive)
CASUAL_KEYWORDS = [
    'personal', 'family', 'church', 'vacation', 'holiday', 'fantasy',
    'congratulations', 'birthday', 'wedding', 'baby', 'anniversary',
    'hobby', 'sport', 'game', 'social', 'friend', 'reunion', 'party',
    'entertainment', 'leisure', 'hobby', 'golf', 'tennis', 'football',
    'baseball', 'soccer', 'recreation', 'club'
]


def extract_folder_from_path(file_path: str) -> tuple:
    """
    Parse file path to extract user ID and folder name.
    
    Args:
        file_path: Path like "allen-p/_sent_mail/123."
        
    Returns:
        Tuple of (user_id, folder_name)
    """
    try:
        parts = file_path.split('/')
        if len(parts) >= 2:
            user_id = parts[0]
            folder_name = parts[1]
            return user_id, folder_name
        elif len(parts) == 1:
            # Some paths might not have folders
            return parts[0], 'unknown'
        else:
            return 'unknown', 'unknown'
    except:
        return 'unknown', 'unknown'


def classify_folder_as_casual(folder_name: str) -> bool:
    """
    Determine if folder name indicates a casual/personal email.
    
    Args:
        folder_name: Name of the folder
        
    Returns:
        True if casual, False if business
    """
    folder_lower = folder_name.lower()
    
    # Check if any casual keyword is in the folder name
    for keyword in CASUAL_KEYWORDS:
        if keyword in folder_lower:
            return True
    
    return False


def download_enron_from_kaggle(data_dir: str) -> str:
    """
    Download Enron dataset from Kaggle using kagglehub API.
    
    Args:
        data_dir: Directory to store the dataset
        
    Returns:
        Path to the emails.csv file
    """
    if not KAGGLE_AVAILABLE:
        raise ImportError("kagglehub is required. Install with: pip install kagglehub")
    
    print("Downloading Enron dataset from Kaggle...")
    print("Note: This requires Kaggle API credentials (kaggle.json)")
    
    # Download latest version of dataset
    path = kagglehub.dataset_download("wcukierski/enron-email-dataset")
    print(f"Downloaded to: {path}")
    
    # Check if it's a ZIP file and extract
    if path.endswith(".zip"):
        extract_dir = os.path.join(data_dir, "enron_dataset")
        os.makedirs(extract_dir, exist_ok=True)
        
        print(f"Extracting ZIP file to {extract_dir}...")
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("Extraction complete!")
        
        csv_file = os.path.join(extract_dir, "emails.csv")
    else:
        # Already extracted
        extract_dir = path
        csv_file = os.path.join(extract_dir, "emails.csv")
    
    # Verify the file exists
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"emails.csv not found in {extract_dir}")
    
    print(f"Enron CSV located at: {csv_file}")
    return csv_file


def load_enron_csv(csv_path: str = None, data_dir: str = None, use_kaggle: bool = False) -> pd.DataFrame:
    """
    Load Enron CSV file with increased field size limit.
    Can download from Kaggle if file doesn't exist locally.
    
    Args:
        csv_path: Path to enron_emails.csv (if None and use_kaggle=True, downloads from Kaggle)
        data_dir: Directory for data storage (used when downloading from Kaggle)
        use_kaggle: If True, download from Kaggle if local file doesn't exist
        
    Returns:
        DataFrame with 'file' and 'message' columns
    """
    # If csv_path provided and exists, use it
    if csv_path and os.path.exists(csv_path):
        print(f"Loading Enron CSV from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} emails from Enron dataset")
        return df
    
    # If file doesn't exist and use_kaggle is True, download from Kaggle
    if use_kaggle:
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Data')
        
        csv_path = download_enron_from_kaggle(data_dir)
        print(f"Loading Enron CSV from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} emails from Enron dataset")
        return df
    
    # Neither local file exists nor Kaggle download requested
    if csv_path:
        raise FileNotFoundError(f"Enron CSV not found at {csv_path}. Use use_kaggle=True to download from Kaggle.")
    else:
        raise ValueError("Must provide csv_path or set use_kaggle=True")


def process_enron_dataset(csv_path: str = None, output_path: str = None, max_emails: int = None, 
                          data_dir: str = None, use_kaggle: bool = False) -> pd.DataFrame:
    """
    Process Enron email dataset with cleaning and labeling.
    
    Args:
        csv_path: Path to enron_emails.csv (optional if use_kaggle=True)
        output_path: Optional path to save intermediate results
        max_emails: Optional limit on number of emails to process (for testing)
        data_dir: Directory for data storage (used when downloading from Kaggle)
        use_kaggle: If True, download from Kaggle if local file doesn't exist
        
    Returns:
        DataFrame with processed emails
    """
    # Load data
    df = load_enron_csv(csv_path, data_dir, use_kaggle)
    
    # Limit for testing if specified
    if max_emails:
        print(f"Limiting to first {max_emails} emails for testing...")
        df = df.head(max_emails)
    
    processed_emails = []
    errors = 0
    
    print("Processing Enron emails...")
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing Enron"):
        try:
            file_path = row['file']
            raw_email = row['message']
            
            # Extract metadata from path
            user_id, folder_name = extract_folder_from_path(file_path)
            
            # Classify as casual or business
            is_casual = classify_folder_as_casual(folder_name)
            label = 'casual' if is_casual else 'business'
            
            # Clean email
            cleaned = clean_email_text(raw_email)
            
            # Skip if email text is too short (likely corrupted)
            if len(cleaned['email_text'].strip()) < 10:
                continue
            
            # Create processed record
            processed_emails.append({
                'email_text': cleaned['email_text'],
                'label': label,
                'source': 'enron',
                'user_id': user_id,
                'folder_name': folder_name,
                'from': cleaned['from'],
                'to': cleaned['to'],
                'subject': cleaned['subject'],
                'date': cleaned['date']
            })
            
        except Exception as e:
            errors += 1
            if errors <= 10:  # Print first 10 errors
                print(f"Error processing row {idx}: {str(e)[:100]}")
            continue
    
    print(f"\nProcessed {len(processed_emails)} emails successfully")
    print(f"Encountered {errors} errors")
    
    # Create DataFrame
    result_df = pd.DataFrame(processed_emails)
    
    # Print label distribution
    print("\nLabel distribution:")
    print(result_df['label'].value_counts())
    
    print("\nTop 20 folders:")
    print(result_df['folder_name'].value_counts().head(20))
    
    # Save if output path specified
    if output_path:
        print(f"\nSaving to {output_path}...")
        result_df.to_pickle(output_path)
        print("Saved!")
    
    return result_df


if __name__ == "__main__":
    # Test with first 1000 emails
    import os
    
    # Get absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_dir, 'Data', 'enron_emails.csv')
    output_path = os.path.join(base_dir, 'Data', 'temp_enron_test.pkl')
    
    print(f"Testing Enron processor...")
    print(f"CSV path: {csv_path}")
    
    # Process first 1000 for testing
    df = process_enron_dataset(csv_path, output_path, max_emails=1000)
    
    print(f"\nSample processed email:")
    print(df.iloc[0]['email_text'][:500])

