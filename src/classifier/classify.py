import requests
from typing import List, Dict, Any

# API endpoint for the HuggingFace Space classifier
API_URL = "https://EtSandoval-emailshifter-api.hf.space/predict"

# Counter for logging
_request_count = 0


def _server_label(text: str) -> Dict[str, Any]:
    """
    Call the classification API and return label + confidence.
    Returns: {"label": 0 or 1, "confidence": float}
    
    Includes detailed logging to help diagnose API issues.
    """
    global _request_count
    _request_count += 1
    
    text_data = {"text": text}
    text_preview = text[:100] + "..." if len(text) > 100 else text
    
    print(f"[Classifier #{_request_count}] Sending request to API...")
    print(f"[Classifier #{_request_count}] Text preview: {text_preview}")
    
    try:
        response = requests.post(
            API_URL, 
            json=text_data,
            timeout=30  # Increased timeout for sleeping HuggingFace Spaces
        )
        
        # Log response status
        print(f"[Classifier #{_request_count}] Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[Classifier #{_request_count}] ERROR: Non-200 response")
            print(f"[Classifier #{_request_count}] Response body: {response.text[:500]}")
            return {"label": 0, "confidence": 0.5}
        
        # Try to parse JSON response
        try:
            result = response.json()
            print(f"[Classifier #{_request_count}] API Response: {result}")
        except ValueError as json_err:
            print(f"[Classifier #{_request_count}] ERROR: Invalid JSON response: {json_err}")
            print(f"[Classifier #{_request_count}] Raw response: {response.text[:500]}")
            return {"label": 0, "confidence": 0.5}
        
        # Extract label and confidence
        label = result.get("label", 0)
        confidence = result.get("confidence", 0.5)
        
        classification = "BUSINESS" if label == 1 else "PERSONAL"
        print(f"[Classifier #{_request_count}] Result: {classification} (confidence: {confidence:.2%})")
        
        return {
            "label": label,
            "confidence": confidence
        }
        
    except requests.exceptions.Timeout:
        print(f"[Classifier #{_request_count}] ERROR: Request timed out after 30s")
        print(f"[Classifier #{_request_count}] The HuggingFace Space may be sleeping - try again in a minute")
        return {"label": 0, "confidence": 0.5}
    
    except requests.exceptions.ConnectionError as conn_err:
        print(f"[Classifier #{_request_count}] ERROR: Connection failed: {conn_err}")
        return {"label": 0, "confidence": 0.5}
    
    except Exception as e:
        print(f"[Classifier #{_request_count}] ERROR: {type(e).__name__}: {e}")
        return {"label": 0, "confidence": 0.5}


def classify(emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Classify emails into business and personal categories.
    
    Args:
        emails: List of email dicts from fetch_recent_emails()
        
    Returns:
        {
            "business": [emails with label=1],
            "personal": [emails with label=0]
        }
        Each email dict includes added fields:
        - "classification": "business" or "personal"
        - "confidence": float (0-1)
    """
    global _request_count
    _request_count = 0  # Reset counter for each batch
    
    print(f"\n{'='*60}")
    print(f"[Classifier] Starting classification of {len(emails)} emails")
    print(f"[Classifier] API endpoint: {API_URL}")
    print(f"{'='*60}\n")
    
    business_list = []
    personal_list = []
    
    for i, email in enumerate(emails, 1):
        print(f"\n--- Email {i}/{len(emails)} ---")
        text = "Subject: " + str(email.get('subject', '')) + " Body: " + str(email.get('body', ''))
        result = _server_label(text)
        
        # Add classification info to email
        email_with_class = email.copy()
        email_with_class["classification"] = "business" if result["label"] == 1 else "personal"
        email_with_class["confidence"] = result["confidence"]
        
        if result["label"] == 1:
            business_list.append(email_with_class)
        else:
            personal_list.append(email_with_class)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"[Classifier] CLASSIFICATION COMPLETE")
    print(f"[Classifier] Total: {len(emails)} | Business: {len(business_list)} | Personal: {len(personal_list)}")
    print(f"{'='*60}\n")
    
    return {
        "business": business_list,
        "personal": personal_list
    }


def classify_single(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify a single email and return it with classification info added.
    """
    text = "Subject: " + email['subject'] + " Body: " + email['body']
    result = _server_label(text)
    
    email_with_class = email.copy()
    email_with_class["classification"] = "business" if result["label"] == 1 else "personal"
    email_with_class["confidence"] = result["confidence"]
    
    return email_with_class