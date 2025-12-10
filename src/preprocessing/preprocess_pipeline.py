"""
Simplified preprocessing pipeline script.
Outputs a dictionary {email_text: label} and metadata CSV.
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from process_enron import process_enron_dataset
from process_spam_assassin import process_spam_assassin_dataset
from build_dataset import (
    combine_datasets,
    create_text_label_dict,
    create_balanced_dict,
    save_dict_as_pickle,
    save_dict_as_json,
    save_metadata_csv,
    generate_dataset_statistics
)

# Add classifier path for rule-based imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'classifier'))
from rule_based import reclassify_dataset, analyze_dataset


def get_paths(base_dir: str = None):
    """
    Get all necessary file paths.
    
    Args:
        base_dir: Base project directory (defaults to project root)
        
    Returns:
        Dictionary of paths
    """
    if base_dir is None:
        # Get project root (two directories up from this file)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    paths = {
        'base_dir': base_dir,
        'data_dir': os.path.join(base_dir, 'Data'),
        'enron_csv': os.path.join(base_dir, 'Data', 'enron_emails.csv'),
        'temp_enron': os.path.join(base_dir, 'Data', 'temp_enron.pkl'),
        'temp_spam': os.path.join(base_dir, 'Data', 'temp_spam.pkl'),
        'output_dir': os.path.join(base_dir, 'Data', 'processed'),
        'dict_pkl': os.path.join(base_dir, 'Data', 'processed', 'email_label_dict.pkl'),
        'dict_json': os.path.join(base_dir, 'Data', 'processed', 'email_label_dict.json'),
        'dict_balanced_pkl': os.path.join(base_dir, 'Data', 'processed', 'email_label_dict_balanced.pkl'),
        'dict_balanced_json': os.path.join(base_dir, 'Data', 'processed', 'email_label_dict_balanced.json'),
        'metadata_csv': os.path.join(base_dir, 'Data', 'processed', 'metadata.csv')
    }
    
    return paths


def main(max_enron_emails: int = None, skip_enron: bool = False, skip_spam: bool = False, 
         use_kaggle: bool = True, no_kaggle: bool = False, balance_ratio: float = None,
         apply_rules: bool = False, rule_threshold: float = 0.5):
    """
    Simplified preprocessing pipeline.
    
    Args:
        max_enron_emails: Maximum number of Enron emails to process (None = all)
        skip_enron: Skip Enron processing (load from temp file)
        skip_spam: Skip Spam Assassin processing (load from temp file)
        use_kaggle: Download Enron dataset from Kaggle (default: True if local file missing)
        no_kaggle: Disable Kaggle download even if local file is missing
        balance_ratio: If specified, create a balanced dataset with this Business:Casual ratio
        apply_rules: Apply rule-based reclassification to fix mislabeled Enron emails
        rule_threshold: Confidence threshold for rule-based reclassification (0.0-1.0)
    """
    # Handle no_kaggle flag
    if no_kaggle:
        use_kaggle = False
    start_time = time.time()
    print("=" * 70)
    print("SIMPLIFIED EMAIL PREPROCESSING PIPELINE")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get paths
    paths = get_paths()
    print(f"Project directory: {paths['base_dir']}")
    print(f"Data directory: {paths['data_dir']}")
    print(f"Output directory: {paths['output_dir']}")
    print()
    
    # Step 1: Process Enron emails
    print("=" * 70)
    print("STEP 1: Processing Enron Emails")
    print("=" * 70)
    
    if skip_enron and os.path.exists(paths['temp_enron']):
        print(f"Loading Enron data from {paths['temp_enron']}...")
        import pandas as pd
        enron_df = pd.read_pickle(paths['temp_enron'])
        print(f"Loaded {len(enron_df)} Enron emails")
    else:
        # Check if local CSV exists
        csv_exists = os.path.exists(paths['enron_csv'])
        
        # Use Kaggle by default if local file doesn't exist (unless explicitly disabled)
        should_use_kaggle = use_kaggle if csv_exists else True
        
        if not csv_exists:
            print("Local Enron CSV not found. Will download from Kaggle...")
            print("(Use --no-kaggle to disable automatic Kaggle download)")
        
        enron_df = process_enron_dataset(
            csv_path=paths['enron_csv'] if csv_exists else None,
            output_path=paths['temp_enron'],
            max_emails=max_enron_emails,
            data_dir=paths['data_dir'],
            use_kaggle=should_use_kaggle
        )
    
    print()
    
    # Step 2: Process Spam Assassin emails
    print("=" * 70)
    print("STEP 2: Processing Spam Assassin Emails")
    print("=" * 70)
    
    if skip_spam and os.path.exists(paths['temp_spam']):
        print(f"Loading Spam Assassin data from {paths['temp_spam']}...")
        import pandas as pd
        spam_df = pd.read_pickle(paths['temp_spam'])
        print(f"Loaded {len(spam_df)} Spam Assassin emails")
    else:
        spam_df = process_spam_assassin_dataset(
            paths['data_dir'],
            paths['temp_spam']
        )
    
    print()
    
    # Step 3: Combine datasets
    print("=" * 70)
    print("STEP 3: Combining Datasets")
    print("=" * 70)
    
    combined_df = combine_datasets(enron_df, spam_df)
    print()
    
    # Step 4: Encode labels (casual=0, business=1)
    print("=" * 70)
    print("STEP 4: Encoding Labels")
    print("=" * 70)
    
    print("Mapping labels: casual → 0, business → 1")
    combined_df['label'] = combined_df['label'].map({'casual': 0, 'business': 1})
    
    # Verify encoding
    label_counts = combined_df['label'].value_counts()
    print(f"Label distribution after encoding:")
    for label, count in sorted(label_counts.items()):
        label_name = "casual" if label == 0 else "business"
        print(f"  {label} ({label_name}): {count}")
    print()
    
    # Step 5: Create text:label dictionary
    print("=" * 70)
    print("STEP 5: Creating Text-Label Dictionary")
    print("=" * 70)
    
    text_label_dict = create_text_label_dict(combined_df)
    print()
    
    # Step 5.5: Apply rule-based reclassification (if requested)
    if apply_rules:
        print("=" * 70)
        print("STEP 5.5: Rule-Based Reclassification")
        print("=" * 70)
        print(f"Applying rule-based patterns to identify mislabeled business emails...")
        print(f"Confidence threshold: {rule_threshold:.0%}")
        
        # First show analysis
        print("\nAnalyzing dataset...")
        analyze_dataset(text_label_dict)
        
        # Apply reclassification
        text_label_dict = reclassify_dataset(text_label_dict, threshold=rule_threshold, verbose=True)
        print()
    
    # Step 6: Save dictionary
    print("=" * 70)
    print("STEP 6: Saving Dictionary")
    print("=" * 70)
    
    save_dict_as_pickle(text_label_dict, paths['dict_pkl'])
    save_dict_as_json(text_label_dict, paths['dict_json'], sample_only=True)
    print()
    
    # Step 6.5: Create balanced dataset (if requested)
    if balance_ratio is not None:
        print("=" * 70)
        print(f"STEP 6.5: Creating Balanced Dataset (1:{balance_ratio:.1f} ratio)")
        print("=" * 70)
        
        balanced_dict = create_balanced_dict(text_label_dict, ratio=balance_ratio)
        save_dict_as_pickle(balanced_dict, paths['dict_balanced_pkl'])
        save_dict_as_json(balanced_dict, paths['dict_balanced_json'], sample_only=True)
    print()
    
    # Step 7: Save metadata CSV
    print("=" * 70)
    print("STEP 7: Saving Metadata CSV")
    print("=" * 70)
    
    save_metadata_csv(combined_df, paths['metadata_csv'])
    print()
    
    # Step 8: Generate statistics
    print("=" * 70)
    print("STEP 8: Generating Statistics")
    print("=" * 70)
    
    generate_dataset_statistics(combined_df, paths['output_dir'])
    print()
    
    # Done!
    elapsed_time = time.time() - start_time
    print("=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    print(f"\nOutput files:")
    print(f"  1. Dictionary (pickle): {paths['dict_pkl']}")
    print(f"  2. Dictionary (JSON sample): {paths['dict_json']}")
    if balance_ratio is not None:
        print(f"  3. Balanced Dictionary (pickle): {paths['dict_balanced_pkl']}")
        print(f"  4. Balanced Dictionary (JSON sample): {paths['dict_balanced_json']}")
        print(f"  5. Metadata CSV: {paths['metadata_csv']}")
        print(f"  6. Statistics: {paths['output_dir']}/statistics.txt")
    else:
        print(f"  3. Metadata CSV: {paths['metadata_csv']}")
        print(f"  4. Statistics: {paths['output_dir']}/statistics.txt")
    print()
    print("To load the dictionary in Python:")
    print(f"  import pickle")
    print(f"  with open('{paths['dict_pkl']}', 'rb') as f:")
    print(f"      email_dict = pickle.load(f)")
    print()
    print("To load the metadata:")
    print(f"  import pandas as pd")
    print(f"  metadata_df = pd.read_csv('{paths['metadata_csv']}')")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simplified preprocessing pipeline for email classification"
    )
    
    parser.add_argument(
        '--max-enron',
        type=int,
        default=None,
        help='Maximum number of Enron emails to process (default: all)'
    )
    
    parser.add_argument(
        '--skip-enron',
        action='store_true',
        help='Skip Enron processing and load from temp file'
    )
    
    parser.add_argument(
        '--skip-spam',
        action='store_true',
        help='Skip Spam Assassin processing and load from temp file'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with only 1000 Enron emails'
    )
    
    parser.add_argument(
        '--use-kaggle',
        action='store_true',
        default=False,
        help='Force Kaggle download even if local CSV exists'
    )
    
    parser.add_argument(
        '--no-kaggle',
        action='store_true',
        help='Disable Kaggle download (fail if local CSV not found)'
    )
    
    parser.add_argument(
        '--balance-ratio',
        type=float,
        default=None,
        help='Create balanced dataset with Business:Casual ratio (e.g., 5.0 for 1:5)'
    )
    
    parser.add_argument(
        '--apply-rules',
        action='store_true',
        help='Apply rule-based reclassification to fix mislabeled Enron business emails'
    )
    
    parser.add_argument(
        '--rule-threshold',
        type=float,
        default=0.5,
        help='Confidence threshold for rule-based reclassification (0.0-1.0, default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Set max_enron to 1000 if in test mode
    max_enron = 1000 if args.test else args.max_enron
    
    # Run pipeline
    main(
        max_enron_emails=max_enron,
        skip_enron=args.skip_enron,
        skip_spam=args.skip_spam,
        use_kaggle=args.use_kaggle,
        no_kaggle=args.no_kaggle,
        balance_ratio=args.balance_ratio,
        apply_rules=args.apply_rules,
        rule_threshold=args.rule_threshold
    )
