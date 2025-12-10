import requests
from typing import List, Dict, Any


def _server_label(text: str) -> Dict[str, Any]:
    """
    Call the classification API and return label + confidence.
    Returns: {"label": 0 or 1, "confidence": float}
    """
    text_data = {"text": text}
    try:
        response = requests.post(
            "https://EtSandoval-emailshifter-api.hf.space/predict", 
            json=text_data,
            timeout=10
        )
        result = response.json()
        return {
            "label": result.get("label", 0),
            "confidence": result.get("confidence", 0.5)
        }
    except Exception:
        # Default to personal/casual if API fails
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
    business_list = []
    personal_list = []
    
    for email in emails:
        text = "Subject: " + email['subject'] + " Body: " + email['body']
        result = _server_label(text)
        
        # Add classification info to email
        email_with_class = email.copy()
        email_with_class["classification"] = "business" if result["label"] == 1 else "personal"
        email_with_class["confidence"] = result["confidence"]
        
        if result["label"] == 1:
            business_list.append(email_with_class)
        else:
            personal_list.append(email_with_class)
    
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