from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

app = FastAPI(title="Email Classifier API")


MODEL_PATH = "./my_email_classifier"

try:
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
except OSError:
    # Fallback or error message if the model folder isn't found
    print(f"Error: Could not find model at {MODEL_PATH}. Make sure the folder is copied to the container.")

# 3. Define Input Structure
class PredictionRequest(BaseModel):
    text: str

# 4. Define Predict Function
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