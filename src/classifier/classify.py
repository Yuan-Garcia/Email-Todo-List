import requests

def _server_label(text):
    text_data = {"text": text}
    response = requests.post("https://EtSandoval-emailshifter-api.hf.space/predict", json=text_data)
    return response.json()['label']



def classify(emails):
    business_list = []
    for email in emails:
        text = "Subject: " + email['subject'] + " Body: " + email['body']
        label = _server_label(text)
        if label == 1:
            business_list.append(email)

    #pass business_list into LLM
    #todo_list = LLM(business_list)

    #replace with todo_list
    return business_list