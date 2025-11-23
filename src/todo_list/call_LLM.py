# use openAI API calls to get SCD
from openai import OpenAI

def call_LLM(system_prompt, user_prompt, bucket = 0):
    """LLMS model's response to user_prompt considering system_prompt

    :param system_prompt: Prompt to give before conversation (zero-shot or procedural)
    :type system_prompt: str
    :param user_prompt: prompt following system_prompt (transcript of conversation)
    :type user_prompt: str
    :param bucket: determines which port to use for parallelization, defaults to 0
    :type bucket: int, optional
    :return: LLM output
    :rtype: str
    """
    # port = 8080 + bucket
    port = 8080
    callUrl = "http://localhost:" + str(port) + "/v1"
    client = OpenAI(base_url=callUrl, api_key = "dummy_key"
    )

    # POST-ing to HMC servers downstairs
    completion = client.chat.completions.create(
    model="model-identifier",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    )

    # full response with thought process and all settings
    full_response = completion.choices[0].message
    # response with thought process only
    text_only_response = full_response.content

    return text_only_response
