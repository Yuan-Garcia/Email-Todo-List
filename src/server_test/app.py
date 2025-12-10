from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification  # Changed
import torch

app = FastAPI(title="Email Classifier API")

MODEL_PATH = "./my_email_classifier"

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()  # Add this for inference mode
except OSError as e:
    print(f"Error: Could not find model at {MODEL_PATH}. Make sure the folder is copied to the container.")
    raise e  # Re-raise to prevent server from starting with no model

class PredictionRequest(BaseModel):
    text: str

@app.post("/predict")
async def predict(request: PredictionRequest):
    try:
        # Tokenize inputs
        inputs = tokenizer(
            request.text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        # Get model prediction
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
        # Convert logits to probabilities and get the predicted label (0 or 1)
        probabilities = torch.softmax(logits, dim=1)
        predicted_class = torch.argmax(probabilities, dim=1).item()
        
        return {
            "text": request.text,
            "label": predicted_class, # 1 for Positive, 0 for Negative
            "confidence": probabilities[0][predicted_class].item()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Run the server (Only if run directly for local testing)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)