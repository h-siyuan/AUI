"""
CUA (computer-use) prompts (extracted verbatim). Do not modify content.
"""

def build_doubao_prompt(instruction: str) -> str:
    return f"""You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space

click(point='<point>x1 y1</point>')
left_double(point='<point>x1 y1</point>')
right_single(point='<point>x1 y1</point>')
drag(start_point='<point>x1 y1</point>', end_point='<point>x2 y2</point>')
hotkey(key='ctrl c') # Split keys with a space and use lowercase. Also, do not use more than 3 keys in one hotkey action.
type(content='xxx') # Use escape characters \\\\, \\\\\\", and \\\\\\\n in content part to ensure we can parse the content in normal python string format. If you want to submit your input, use \\\\\\\n at the end of content. 
scroll(point='<point>x1 y1</point>', direction='down or up or right or left') # Show more information on the `direction` side.
wait() #Sleep for 5s and take a screenshot to check for any changes.
finished(content='xxx') # Use escape characters \\\\, \\\\\\", and \\\\\\\n in content part to ensure we can parse the content in normal python string format.


## Note
- Use English in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.

## User Instruction
{instruction}"""

def build_operator_prompt(task_description: str, repeat_warning: str,
                          history_context: str, current_step: int, max_steps: int) -> str:
    return f"""Complete this task: {task_description}

{repeat_warning}

Context from previous actions:
{history_context}

Current step: {current_step}/{max_steps}

Please analyze the current state and take the next action to complete the task. If the task appears to be completed successfully, you may finish."""
