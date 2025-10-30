"""
Commenter prompts (extracted verbatim). Do not modify content.
"""

def build_storyboard_prompt(width: int, height: int) -> str:
    return f"""You are analyzing a UI design issue that caused a CUA (Computer Use Agent) policy failure.

You will see two images:
1. The current website state (Resolution: {width}x{height})
2. A storyboard summarizing the failed task attempt, arranged as a grid of step screenshots (variable count) fitted into a 1920x1080 canvas

The storyboard contains:
- Header: Task description and expected outcome
- Grid: A variable number of screenshots (one per step), arranged to fit the canvas
- Below each screenshot: The action taken and agent's thought

Analyze both images to identify concrete UI design problems that caused the failure, then output a compact JSON object with actionable guidance for code changes.

Output strictly as JSON with these keys only:
- issues: array of up to 3 short strings describing the primary UI problems (visibility, accessibility, layout, feedback, interaction, hierarchy)
- actionable_changes: array of 3–6 short, prescriptive changes referencing concrete selectors/IDs and layout adjustments (e.g., "Move #generate-btn above the fold", "Allow plain text in #qr-text", "Do not auto-generate on load", "Make #controls visible in 1280x720")
- fit_within_screen: boolean (true if critical controls should be rearranged to avoid scrolling at 1280x720)
- avoid_regressions: boolean (must be true; changes must not break existing working flows)

Rules:
- Prefer minimal, surgical changes that directly address the failure.
- Do not propose adding strict validation that blocks task inputs; keep validation permissive.
- Do not propose auto-triggered flows on load; initial state should be neutral.
- Keep suggestions specific to the visible UI and layout; no placeholders.

Respond with JSON only, no extra text."""


def build_text_only_prompt(width: int, height: int, task_description: str,
                            expected_outcome: str, steps_text: str, step_count: int) -> str:
    return f"""You are analyzing a UI design issue that caused a CUA (Computer Use Agent) policy failure.

You will see the current website state (Resolution: {width}x{height}) in the image.

The failed task details:
**Task**: {task_description}
**Expected Outcome**: {expected_outcome}

**Agent's {step_count}-step attempt (Action & Thought):**
{steps_text.strip()}

Analyze the image and the step text to identify concrete UI design problems that caused the failure, then output a compact JSON object with actionable guidance for code changes.

Output strictly as JSON with these keys only:
- issues: array of up to 3 short strings describing the primary UI problems (visibility, accessibility, layout, feedback, interaction, hierarchy)
- actionable_changes: array of 3–6 short, prescriptive changes referencing concrete selectors/IDs and layout adjustments (e.g., "Move #generate-btn above the fold", "Allow plain text in #qr-text", "Do not auto-generate on load", "Make #controls visible in 1280x720")
- fit_within_screen: boolean (true if critical controls should be rearranged to avoid scrolling at 1280x720)
- avoid_regressions: boolean (must be true; changes must not break existing working flows)

Rules:
- Prefer minimal, surgical changes that directly address the failure.
- Do not propose adding strict validation that blocks task inputs; keep validation permissive.
- Do not propose auto-triggered flows on load; initial state should be neutral.
- Keep suggestions specific to the visible UI and layout; no placeholders.

Respond with JSON only, no extra text."""


def build_screenshot_only_prompt(width: int, height: int, num_steps: int) -> str:
    return f"""You are analyzing a UI design issue that caused a CUA (Computer Use Agent) policy failure.

You will see multiple images:
1. The first image: Current website state (Resolution: {width}x{height})
2. Following {num_steps} images: Screenshots from each step of the agent's failed interaction attempt

The agent attempted to complete a task by taking actions on the website, but failed. These step screenshots show the visual progression of the agent's interaction attempt.

Analyze all the images to identify concrete UI design problems that caused the failure, then output a compact JSON object with actionable guidance for code changes.

Output strictly as JSON with these keys only:
- issues: array of up to 3 short strings describing the primary UI problems (visibility, accessibility, layout, feedback, interaction, hierarchy)
- actionable_changes: array of 3–6 short, prescriptive changes referencing concrete selectors/IDs and layout adjustments (e.g., "Move #generate-btn above the fold", "Allow plain text in #qr-text", "Do not auto-generate on load", "Make #controls visible in 1280x720")
- fit_within_screen: boolean (true if critical controls should be rearranged to avoid scrolling at 1280x720)
- avoid_regressions: boolean (must be true; changes must not break existing working flows)

Rules:
- Prefer minimal, surgical changes that directly address the failure.
- Do not propose adding strict validation that blocks task inputs; keep validation permissive.
- Do not propose auto-triggered flows on load; initial state should be neutral.
- Keep suggestions specific to the visible UI and layout; no placeholders.

Respond with JSON only, no extra text."""

