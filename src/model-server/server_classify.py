import requests

def classify_email(email_text, server_url="http://<server_ip>:8000/predict"):
    """
    Send email text to the BERT API and return the predicted label.
    """
    payload = {"email_text": email_text}
    response = requests.post(server_url, json=payload)
    
    if response.status_code == 200:
        return response.json()["label"]
    else:
        raise Exception(f"API request failed: {response.status_code}, {response.text}")

# Example usage
if __name__ == "__main__":
    email_text = "Let's schedule a formal meeting with the client tomorrow."
    label = classify_email(email_text)
    print(f"Predicted label: {label}")  # Outputs: "business" or "casual"