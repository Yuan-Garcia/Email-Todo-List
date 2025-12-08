from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import BertForSequenceClassification, BertTokenizer

app = FastAPI(title="Email Classification API")

# Load tokenizer and model
# Use the local tokenizer directory for tokenizer config
TOKENIZER_DIR = "src/classifier/my_email_classifier"
# Use a pre-trained BERT model (replace with your fine-tuned model path when available)
MODEL_NAME = "bert-base-uncased"

tokenizer = BertTokenizer.from_pretrained(TOKENIZER_DIR)
model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
model.eval()

# Define labels
labels = ["casual", "business"]  # 0 -> casual, 1 -> business

# Input schema
class EmailInput(BaseModel):
    email_text: str

# Prediction endpoint
@app.post("/predict")
def predict(input: EmailInput):
    inputs = tokenizer(input.email_text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        # Get the predicted class (0 or 1) using argmax
        predicted_idx = torch.argmax(outputs.logits, dim=1).item()
        predicted_label = labels[predicted_idx]
    return {"label": predicted_label}  # ✅ This is exactly the format the client receives
