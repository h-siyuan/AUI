from typing import List, Optional, Callable

def chat_completion(
    client,
    deployment: str,
    messages: List[dict],
    *,
    max_completion_tokens: int,
    temperature: Optional[float] = None,
) -> str:
    kwargs = {
        "model": deployment,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def chat_stream_completion(
    client,
    deployment: str,
    messages: List[dict],
    *,
    max_completion_tokens: int,
    stream_callback: Callable[[str], None],
) -> str:
    stream = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_completion_tokens=max_completion_tokens,
        stream=True,
    )
    full: List[str] = []
    for chunk in stream:
        try:
            delta = chunk.choices[0].delta
            piece = getattr(delta, 'content', None)
            if piece is None and isinstance(delta, dict):
                piece = delta.get('content')
        except Exception:
            piece = None  # type: ignore
        if piece:
            full.append(piece)
            try:
                stream_callback(piece)
            except Exception:
                pass
    return "".join(full)

