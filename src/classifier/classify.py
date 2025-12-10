import requests


#API_URL = "https://advik-mareedu-emailshifter-api.hf.space/predict"
API_URL = "https://EtSandoval-emailshifter-api.hf.space/predict"


# text_data = {"text": "Subject: iso skateboard, it’s the one in the photo (look how happy i was… not anymore because someone stole it during casemas) jadyn “should’ve known better” long"}

# response = requests.post(API_URL, json=text_data)

# if response.status_code == 200:
#     print(response.json()) 
# else:
#     print("Error:", response.status_code)
#     print(response.text)

emails = [{'from': 'ACM Learning Center <learning@acm.org>', 'subject': 'January 13 Talk: "How to Extract Meaningful Insights from Data" with Angelica Lo Duca, Researcher and Author', 'date': 'Tue, 9 Dec 2025 08:00:00 -0500 (EST)', 'body': '--------------------------------------------------------------------------------------------------------------------------\nJanuary 13 Talk: "How to Extract Meaningful Insights from Data" with Angelica Lo Duca, Researcher and Author\n--------------------------------------------------------------------------------------------------------------------------\n\nRegister now for the next free ACM TechTalk, "How to Extract Meaningful Insights from Data" (https://events.zoom.us/ev/AnVWkl_U-CxgGyPj9q_-i68HOJGFWwiUKKUsxY3hKq_zlAfgcmz-~AqIkLPCyvSeInFpIJynBvZcWQO8hhHS2UIs3bPP5M6KltfMMnckSTIRYcA), presented on Tuesday, January 13 at 12:00 PM ET/17:00 UTC by Angelica Lo Duca, Researcher at the Institute of Informatics and Telematics of the National Research Council, Italy. Victor Yocco, UX Researcher at ServiceNow, will moderate the questions and answers session following the talk.\n\nLeave your comments and questions with our speaker now and any time before the live event on ACM\'s Discourse Page (https://on.acm.org/t/how-to-extract-meaningful-insights-from-data/3500). And check out the page after the webcast for extended discussion with your peers in the computing community, as well as further resources on on data extraction, data visualization, and more.\n\n(If you\'d like to attend but can\'t make it to the virtual event, you still need to register to receive a recording of the TechTalk when it becomes available.)\n\nFollowing the previous talk, "Applying Cinematic Techniques to Data Storytelling" (5 March 2025), several questions emerged about the stage that precedes data storytelling. Participants expressed a strong interest in understanding how a relevant insight can be extracted from data before any narrative or visualization step takes place. Many books and presentations describe the nature and value of insights, yet few address the fundamental techniques for discovering them in real datasets.\n\nThis talk will focus on practical, accessible methods for guiding the transition from raw data to insights that inform decisions. The session will present clear analytical strategies, illustrate their rationale, and demonstrate how they can benefit researchers, engineers, and data professionals across domains.\n\nThe session includes:\n-Temporal Analysis. Examination of patterns that develop through time, with attention to shifts, cycles, and discontinuities that reveal structural changes in the data.\n-Zoom Analysis. Exploration of data through different levels of granularity to uncover trends that appear only when the scale changes.\n-Multi-Category Comparison. Evaluation of similarities and differences across several groups, with techniques that help identify contrasts that matter to a given problem.\n-Spatial Analysis. Interpretation of geographic or positional relationships that highlight clusters, distances, or configurations with analytical significance.\n-Outlier Assessment. Detection and interpretation of irregular observations that may indicate errors, hidden mechanisms, or opportunities for discovery.\n\nDuration: 60 minutes (including audience Q&A)\n\nPresenter:\nAngelica Lo Duca, Researcher, Institute of Informatics and Telematics of the National Research Council, Italy\n\nAngelica Lo Duca is a researcher at the Institute of Informatics and Telematics of the National Research Council, Italy. She is also an adjunct professor of Data Journalism at the University of Pisa. She has published over 60 scientific papers at national and international conferences and journals. She is the author of the book "Comet for Data Science" (Packt Publishing Ltd, 2022), co-author of "Learning and Operating Presto" (O\'Reilly Media, 2023), "Data Storytelling with Altair and AI" (Manning Publications, 2024), and "Become a Great Data Storyteller" (Wiley, 2025.)\n\n\nModerator:\nVictor Yocco, UX Researcher, ServiceNow\n\nVictor Yocco holds a PhD in psychology and communication. He is the author of "Design for the Mind" (Manning Publications, 2016) and is currently writing a book for CRC Press on the user experience of agentic AI. He has spent fifteen years as a UX researcher analyzing the overlap between human behavior and digital interfaces.\n\nVisit learning.acm.org/techtalks-archive for our full archive of past TechTalks.\nYou are subscribed with: ygarcia@g.hmc.edu\n\nUnsubscribe:  https://optout.acm.org/unsubscribe.cfm?rm=BIuGuLLE0F81F1C74E06D73122DEB76A8248255477266684B43644851484B4D70444F56&ln=ACM-WEBINAR'}]
def server_label(text):
    text_data = {"text": text}
    response = requests.post("https://EtSandoval-emailshifter-api.hf.space/predict", json=text_data)
    print(response.json()['label'])

server_label('bruh')


def classify(emails):
    business_list = []
    for email in emails:
        text = "Subject: " + email['subject'] + " " + email['body']
        print(text)
        label = server_label(email)
        if label == 1:
            business_list.append(email)
    
    #pass business_list into LLM

    return business_list

classify(emails)