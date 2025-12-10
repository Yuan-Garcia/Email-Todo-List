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
        casual_examples = [
            # --- 20 CASUAL/PERSONAL EMAILS ---
            "Hey! Want to grab dinner later? I'm craving Thai food.",
            "Yo what's up? You tryna play basketball this weekend?",
            "Mom, I landed safely. Love you.",
            "Happy birthday bro!!! Hope it's the best one yet!",
            "Can you send me the pics from last night? They were so funny 😂",
            "Hey dude I'm outside, come down when you're ready.",
            "Miss you, hope we can catch up soon!",
            "I forgot my charger at your place — can you bring it tmr?",
            "That movie we watched was actually so good lol",
            "I'm thinking of dyeing my hair red. Thoughts?",
            "Hey wanna go thrifting on Saturday??",
            "Thanks for listening to me rant last night. Needed that fr.",
            "Do you still have my hoodie? If so, KEEP IT — it looks better on you.",
            "Game night at my place tonight?? We have snacks + Mario Kart.",
            "Bro why did you eat the last slice of pizza be honest",
            "Tell me why my professor assigned a 10 page paper LAST MINUTE 😭",
            "Can you feed the cat while I'm gone? Her food is under the sink.",
            "We should plan a road trip this summer. For real this time.",
            "I just saw the funniest TikTok and immediately thought of you",
            "I'm so proud of you. Just wanted you to know that."
        ]

        business_examples = [
            # --- 20 BUSINESS/PROFESSIONAL EMAILS ---
            "Attached is the updated proposal for your review. Please share feedback by EOD Thursday.",
            "Hi team, reminder that our sprint planning meeting starts at 9 AM sharp.",
            "Thank you for your interest. Our recruiting team will follow up regarding next steps.",
            "Please find attached the signed contract along with the revised scope of work.",
            "Good morning, reaching out to schedule a demo for next week — are you available Tuesday at 2 PM?",
            "We appreciate your patience while we investigate this issue. We will update you shortly.",
            "Per your request, I have updated the documentation and pushed the changes to GitHub.",
            "Hello, confirming that your order has shipped and is expected to arrive by Friday.",
            "Following up on my previous email — do you have an update on the approval status?",
            "Thank you for the opportunity to present today. It was a pleasure speaking with your team.",
            "Dear committee members, the quarterly report draft is now ready for review.",
            "We will need confirmation from finance before moving forward with procurement.",
            "Hi all, reminder to complete your cybersecurity training by the end of the month.",
            "Could you provide a timeline for delivery so we can plan resources accordingly?",
            "Congratulations — your fellowship application has been accepted!",
            "Our records show an outstanding balance of $420. Please remit payment at your earliest convenience.",
            "Attached is the onboarding schedule for new hires starting next Monday.",
            "Thank you for your feedback. I have incorporated the suggested changes into the final document.",
            "Please let me know if you'd prefer Zoom or in-person for tomorrow's discussion.",
            "Kindly review the attached invoice and confirm once processed."
        ]

        
        print("\n" + "="*60)
        print("Demo Classification Results")
        print("="*60)
        
        print("\n CASUAL \n")
        for text in casual_examples:
            result = classifier.classify(text)
            display_text = f'"{text[:60]}..."' if len(text) > 60 else f'"{text}"'
            print(f"\nText: {display_text}")
            print(f"   -> {result['label'].upper()} ({result['confidence']:.1%})")

        print("\n BUSINESS \n")

        for text in business_examples:
            result = classifier.classify(text)
            display_text = f'"{text[:60]}..."' if len(text) > 60 else f'"{text}"'
            print(f"\nText: {display_text}")
            print(f"   -> {result['label'].upper()} ({result['confidence']:.1%})")


if __name__ == "__main__":
    main()

