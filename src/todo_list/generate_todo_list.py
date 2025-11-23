from call_LLM import call_LLM

def generate_todo_list(email_list):
    system_email_prompt = """
    You are an assistant that converts raw emails into a concise, prioritized to-do list.
    Your goal is to analyze the content of each email, infer the sender’s intent, 
    and identify all actionable items. You must only output information grounded in the 
    emails—no hallucinated tasks.
    """

    user_email_prompt = f"""
    You are given a list of emails. For each email:

    1. Extract **all explicit tasks** (e.g., “submit your forms,” “schedule a meeting,” “send the report”).
    2. Infer **implicit tasks** when reasonable (e.g., if someone is asking a question, the task might be “respond with X”).
    3. Prioritize tasks by urgency and importance using:

    * time deadlines
    * sender authority (e.g., boss > colleague > automated marketing)
    * relevance to ongoing responsibilities
    * urgency implied by language (“asap”, “need this today”, etc.)
    4. Deduplicate similar tasks across emails.
    5. Write tasks in clear, concise, imperative style.
    6. For each task, include:

    * **Description**
    * **Source email** (sender + subject)
    * **Priority**: High | Medium | Low
    * **Deadline**: Explicit or inferred (or “None”)

    Your output **must** be formatted as:

    ```
    TO-DO LIST
    ====================

    1. [PRIORITY] Task description  
    - Source: <sender> — <subject>  
    - Deadline: <date or None>

    2. ...
    ```

    **Emails:**

    {email_list}
    """

    return call_LLM(system_email_prompt, user_email_prompt)

def main():
    # Example usage
    emails = ["I need you to do something TODAY!!!", "Can you send me the report by next week?"]
    todo_list = generate_todo_list(emails)
    print(todo_list)

if __name__ == "__main__":
    main()