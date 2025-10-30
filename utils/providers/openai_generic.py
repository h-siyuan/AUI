from typing import List, Optional

def chat_completion(
    client,
    model: str,
    messages: List[dict],
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

