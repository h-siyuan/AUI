"""
VLM verifier prompts (extracted verbatim). Do not modify content.
"""

def build_verifier_screenshot_only_prompt(task_desc: str) -> str:
    return (
        "You are a strict evaluator. Decide if the task was completed by inspecting the screenshots. "
        "Do not assume hidden state; rely only on visible evidence in the screenshots. If uncertain, answer fail. "
        "Output strict JSON only.\n\n"
        f"Task:\n{task_desc}\n\n"
        "Evidence:\n- You will receive a time-ordered sequence of screenshots (earliest to latest).\n"
        "- Use only the visible content in these images.\n\n"
        "Judgment rule:\n- Mark pass only if the final visible UI clearly shows task completion.\n"
        "- If the screenshots are ambiguous or do not visibly confirm completion, mark fail.\n\n"
        "Output JSON schema (no extra text):\n"
        '{"verdict":"pass|fail","confidence":0.0-1.0,"reason":"short, factual","used_screenshots":[indices]}'
    )


def build_verifier_screenshot_expected_prompt(task_desc: str, expected_text: str) -> str:
    return (
        "You are a strict evaluator. Decide if the final UI state matches the expected outcome, using only the screenshots. "
        "Do not assume hidden state. If uncertain, answer fail. Output strict JSON only.\n\n"
        f"Task:\n{task_desc}\n\n"
        f"Expected outcome:\n{expected_text}\n\n"
        "Evidence:\n- Time-ordered screenshots (earliest to latest).\n- Use only the visible content in these images.\n\n"
        "Judgment rule:\n- Mark pass only if the screenshots clearly show the expected outcome is satisfied in the final state.\n"
        "- If evidence is ambiguous or insufficient, mark fail.\n\n"
        "Output JSON schema (no extra text):\n"
        '{"verdict":"pass|fail","confidence":0.0-1.0,"reason":"short, factual","used_screenshots":[indices]}'
    )

