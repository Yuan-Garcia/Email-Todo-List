from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import BertForSequenceClassification, BertTokenizer

app = FastAPI(title="Email Classification API")

# Load tokenizer and model
MODEL_DIR = "src/classifier/my_email_classifier/model.safetensors"
tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
model = BertForSequenceClassification.from_pretrained(MODEL_DIR, device_map="auto")
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
        probs = torch.sigmoid(outputs.logits)    # Binary classification
        predicted_val = probs.round().item()
        predicted_label = labels[int(predicted_val)]
    return {"label": predicted_label}  # ✅ This is exactly the format the client receives
