"""
Judge prompts (extracted verbatim). Do not modify content.
"""

def build_analyze_prompt(html_content: str, tasks_text: str) -> str:
    return f"""You are a Judge Agent in the AUI evaluation pipeline. Your role is to analyze HTML websites and determine which tasks can be realistically completed using the existing UI elements.

## YOUR ROLE AND RESPONSIBILITIES

You are evaluating whether a generated website can support specific user tasks. This evaluation directly impacts the quality metrics of the AUI system:
- You determine which tasks are "supportable" (have sufficient UI elements for completion)
- You create testable rules that can be evaluated programmatically
- Your analysis feeds into automated testing by CUA policy agents

## TASK SUPPORTABILITY CRITERIA

**A task is SUPPORTABLE if:**
- The website contains the necessary UI elements (buttons, inputs, displays) for task completion
- The JavaScript functionality exists or can reasonably be inferred to exist
- The task can be completed through standard web interactions (clicks, typing, navigation)
- Even partial implementations should be considered supportable if core functionality exists

**A task is UNSUPPORTABLE if:**
- Essential UI elements are completely missing (e.g., no input fields for data entry tasks)
- The task requires functionality that is clearly not implemented (e.g., file upload with no input element)
- The website structure makes task completion impossible

## ANALYSIS GUIDELINES

**When analyzing HTML and JavaScript:**
1. Look for relevant input elements (text fields, buttons, selectors, sliders)
2. Identify display elements for showing results (divs with IDs, score displays, status indicators)
3. Check for event handlers and JavaScript functions that suggest functionality
4. Consider that modern web development often adds functionality dynamically
5. Assume standard web behaviors work (form submission, button clicks, etc.)

**Handling incomplete implementations:**
- If core UI elements exist, assume basic functionality works
- Missing styling or advanced features should not make tasks unsupportable
- Focus on whether the essential user workflow can be completed
- Consider that JavaScript might add functionality not visible in static HTML

## RULE CREATION STANDARDS

**Rules must be:**
- **Testable in browser DOM**: Use selectors that can be evaluated (e.g., "#score", ".result-display")
- **Specific and unambiguous**: Avoid vague conditions
- **Match the task's success criteria**: Focus on the end goal, not intermediate steps
- **Simple syntax**: Use basic comparisons (>, ==, !=, contains, exists)

**Rule format examples:**
- Numeric comparisons: "#score > 0", "#points >= 100"
- Text content: "#result-text contains 'Success'", "#status-display != 'Error'"
- Element existence: "#completion-badge exists"
- Complex conditions: "#timer-display contains ':' AND #game-status == 'running'"

**Rule style (MANDATORY): Hybrid OR**
- If an attribute predicate best captures completion (e.g., "#downloadBtn[href^='data:'] exists", "#btnStart[aria-disabled] == 'false'"), emit a single rule composed as:
  - PRIMARY attribute predicate OR SECONDARY id-text/number proxy.
  - The proxy must be a visible element with a stable id updated synchronously to reflect the same completion (e.g., "#downloadStatus contains 'enabled'", "#solveStatus == 'done'").
- If no attribute predicate is necessary, emit a single id-based text/number/boolean rule.
- Emit exactly one rule string per task; do not output multiple separate rules.

**Avoid overly complex rules that:**
- Require multiple DOM manipulations
- Depend on specific timing or animations
- Use advanced JavaScript evaluation

## OUTPUT FORMAT

HTML:
{html_content}

TASKS:
{tasks_text}

Analyze each task thoroughly and respond with a JSON array. Each item must have:
- task_index: number (1-based)
- task_description: string (copy the original task description)
- expected_outcome: string (describe what successful completion should look like)
- supportable: true/false
- rule: simple completion rule if supportable (empty string if not supportable)
- reason: detailed explanation of why the task is or isn't supportable (minimum 2-3 sentences)

Output only the JSON array with no additional text."""


def build_analyze_three_component_prompt(html_content: str, tasks_text: str, analysis_instruction: str) -> str:
    return f"""You are a Judge Agent in the AUI evaluation pipeline. Your role is to analyze HTML websites and determine which tasks can be realistically completed using the existing UI elements.

## YOUR ROLE AND RESPONSIBILITIES

You are evaluating whether a generated website can support specific user tasks. This evaluation directly impacts the quality metrics of the AUI system:
- You determine which tasks are "supportable" (have sufficient UI elements for completion)
- You create testable rules that can be evaluated programmatically
- Your analysis feeds into automated testing by CUA policy agents

## TASK SUPPORTABILITY CRITERIA

**A task is SUPPORTABLE if:**
- The website contains the necessary UI elements (buttons, inputs, displays) for task completion
- The JavaScript functionality exists or can reasonably be inferred to exist
- The task can be completed through standard web interactions (clicks, typing, navigation)
- Even partial implementations should be considered supportable if core functionality exists

**A task is UNSUPPORTABLE if:**
- Essential UI elements are completely missing (e.g., no input fields for data entry tasks)
- The task requires functionality that is clearly not implemented (e.g., file upload with no input element)
- The website structure makes task completion impossible

## ANALYSIS GUIDELINES

**When analyzing HTML and JavaScript:**
1. Look for relevant input elements (text fields, buttons, selectors, sliders)
2. Identify display elements for showing results (divs with IDs, score displays, status indicators)
3. Check for event handlers and JavaScript functions that suggest functionality
4. Consider that modern web development often adds functionality dynamically
5. Assume standard web behaviors work (form submission, button clicks, etc.)

**Handling incomplete implementations:**
- If core UI elements exist, assume basic functionality works
- Missing styling or advanced features should not make tasks unsupportable
- Focus on whether the essential user workflow can be completed
- Consider that JavaScript might add functionality not visible in static HTML

## RULE CREATION STANDARDS

**Rules must be:**
- **Testable in browser DOM**: Use selectors that can be evaluated (e.g., "#score", ".result-display")
- **Specific and unambiguous**: Avoid vague conditions
- **Match the task's success criteria**: Focus on the end goal, not intermediate steps
- **Simple syntax**: Use basic comparisons (>, ==, !=, contains, exists)

**Rule format examples:**
- Numeric comparisons: "#score > 0", "#points >= 100"
- Text content: "#result-text contains 'Success'", "#status-display != 'Error'"
- Element existence: "#completion-badge exists"
- Complex conditions: "#timer-display contains ':' AND #game-status == 'running'"

**Avoid overly complex rules that:**
- Require multiple DOM manipulations
- Depend on specific timing or animations
- Use advanced JavaScript evaluation

## OUTPUT FORMAT

HTML:
{html_content}

TASKS:
{tasks_text}

{analysis_instruction}

Output only the JSON array with no additional text."""


def build_single_rule_prompt(task_description: str, html_content: str) -> str:
    return f"""You are a Judge Agent analyzing whether this specific task can be completed on the given website.

## ANALYSIS REQUIREMENTS

**Evaluate supportability based on:**
- Are the necessary UI elements present for this task?
- Can the task be completed through standard web interactions?
- Does the website structure support the required user workflow?

**Be optimistic**: If core elements exist, assume basic functionality works.

## RULE CREATION GUIDELINES

**Create testable rules that:**
- Use simple DOM selectors (e.g., "#score", ".result")
- Focus on end-state verification (what indicates task completion)
- Use basic operators: >, ==, !=, contains, exists
- Can be evaluated programmatically in browser

**Rule style (MANDATORY): Hybrid OR**
- If an attribute predicate best captures completion (e.g., "#downloadBtn[href^='data:'] exists", "#btnStart[aria-disabled] == 'false'"), emit a single rule composed as:
  - PRIMARY attribute predicate OR SECONDARY id-text/number proxy.
  - The proxy must be a visible element with a stable id updated synchronously to reflect the same completion (e.g., "#downloadStatus contains 'enabled'", "#solveStatus == 'done'").
- If no attribute predicate is necessary, emit a single id-based text/number/boolean rule.

**Examples:**
- "#score > 0" (for score-based tasks)
- "#result-display contains 'Success'" (for completion status)
- "#timer-display != '00:00'" (for timer-based tasks)

TASK: {task_description}

HTML:
{html_content}

Respond with JSON only:
{{"task_description": "copy the task description", "expected_outcome": "what successful completion should look like", "supportable": true/false, "rule": "simple_rule_string", "reason": "detailed explanation"}}

If supportable, provide a testable rule. If not supportable, use empty string for rule."""
