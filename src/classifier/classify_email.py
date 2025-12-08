"""
Email Classifier - Inference Script

Classifies emails as business (1) or casual (0) using the trained BERT model.

Usage:
    python classify_email.py "Your email text here"
    python classify_email.py --interactive  # Interactive mode
    python classify_email.py                 # Demo mode
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import argparse
import os

# Path to your saved model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "my_email_classifier")

# Label mappings
ID2LABEL = {0: "casual", 1: "business"}
LABEL2ID = {"casual": 0, "business": 1}


class EmailClassifier:
    """Wrapper class for email classification inference."""
    
    def __init__(self, model_path: str = MODEL_PATH):
        """
        Initialize the classifier with a trained model.
        
        Args:
            model_path: Path to saved model directory
        """
        print(f"Loading model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()  # Set to evaluation mode
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Model loaded on {self.device}")
    
    def classify(self, text: str) -> dict:
        """
        Classify a single email text.
        
        Args:
            text: Email text to classify
            
        Returns:
            Dictionary with prediction, label, and confidence scores
        """
        # Tokenize
        inputs = self.tokenizer(
            text, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
        
        # Get prediction
        pred_id = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][pred_id].item()
        
        return {
            "prediction": pred_id,
            "label": ID2LABEL[pred_id],
            "confidence": confidence,
            "probabilities": {
                "casual": probabilities[0][0].item(),
                "business": probabilities[0][1].item()
            }
        }
    
    def classify_batch(self, texts: list) -> list:
        """
        Classify multiple emails at once.
        
        Args:
            texts: List of email texts
            
        Returns:
            List of prediction dictionaries
        """
        return [self.classify(text) for text in texts]


def main():
    parser = argparse.ArgumentParser(description="Classify emails as business or casual")
    parser.add_argument("text", nargs="?", help="Email text to classify")
    parser.add_argument("--interactive", "-i", action="store_true", 
                        help="Run in interactive mode")
    parser.add_argument("--model-path", default=MODEL_PATH,
                        help="Path to trained model directory")
    args = parser.parse_args()
    
    # Initialize classifier
    classifier = EmailClassifier(args.model_path)
    
    if args.interactive:
        print("\n" + "="*60)
        print("Email Classifier - Interactive Mode")
        print("Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            text = input("\nEnter email text (or 'quit'): ").strip()
            if text.lower() == 'quit':
                break
            if not text:
                continue
                
            result = classifier.classify(text)
            print(f"\nClassification: {result['label'].upper()}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Casual prob: {result['probabilities']['casual']:.1%}")
            print(f"   Business prob: {result['probabilities']['business']:.1%}")
    
    elif args.text:
        result = classifier.classify(args.text)
        print(f"\nClassification: {result['label'].upper()}")
        print(f"   Confidence: {result['confidence']:.1%}")
    
    else:
        # Demo with example texts
        examples = [
            "Hey! Want to grab lunch tomorrow? The weather looks great!",
            "Please find attached the Q3 financial report for your review. The board meeting is scheduled for Monday at 2pm.",
            "LOL that was hilarious! See you at the party tonight",
            "Per our discussion, I've updated the project timeline. Please confirm receipt and let me know if you have any concerns regarding the deliverables."
        ]
        
        print("\n" + "="*60)
        print("Demo Classification Results")
        print("="*60)
        
        for text in examples:
            result = classifier.classify(text)
            display_text = f'"{text[:60]}..."' if len(text) > 60 else f'"{text}"'
            print(f"\nText: {display_text}")
            print(f"   -> {result['label'].upper()} ({result['confidence']:.1%})")


if __name__ == "__main__":
    main()

