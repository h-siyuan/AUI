import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.browser import BrowserController
from .base_cua_policy import BaseCUAPolicy
from .prompts.cua_prompts import build_operator_prompt

class OperatorCUAPolicy(BaseCUAPolicy):
    def __init__(self, model_client, cua_model_name: str = "operator", max_steps: int = 10):
        """OpenAI Computer Use Agent Policy"""
        super().__init__(model_client, cua_model_name, max_steps)
        self.cua_model_name = cua_model_name
        # Align tool and browser viewport to 1280x720
        self.display_width = 1280
        self.display_height = 720
        # Maintain loop state for operator Responses API
        self._last_response_id: Optional[str] = None
        self._last_call_id: Optional[str] = None

    async def execute_task(self, app_name: str, model_name: str, website_url: str,
                           task: Dict[str, Any], completion_rule: str,
                           save_dir: Optional[str] = None) -> Dict[str, Any]:
        """Reset loop state before delegating to base executor"""
        self._last_response_id = None
        self._last_call_id = None
        return await super().execute_task(app_name, model_name, website_url, task, completion_rule, save_dir)
    
    def _build_computer_use_prompt(self, task_description: str, success_criteria: str, 
                                   trajectory: List[Dict], current_step: int) -> str:
        """Build prompt for OpenAI computer-use API"""
        
        # Build history context (but don't include in API - OpenAI manages context)
        history_context = ""
        repeat_warning = ""
        
        if trajectory:
            recent = trajectory[-3:]  # Show recent context
            for i, t in enumerate(recent):
                action = t.get('action', {})
                result = t.get('result', {})
                
                # Convert internal action to readable format
                if action.get('action') == 'left_click':
                    coord = action.get('coordinate', [])
                    if coord:
                        history_context += f"Step {len(trajectory) - len(recent) + i + 1}: Clicked at ({coord[0]}, {coord[1]})"
                elif action.get('action') == 'type':
                    text = action.get('text', '')
                    history_context += f"Step {len(trajectory) - len(recent) + i + 1}: Typed '{text}'"
                elif action.get('action') == 'scroll':
                    pixels = action.get('pixels', 0)
                    direction = 'down' if pixels < 0 else 'up'
                    history_context += f"Step {len(trajectory) - len(recent) + i + 1}: Scrolled {direction}"
                elif action.get('action') == 'terminate':
                    status = action.get('status', 'success')
                    history_context += f"Step {len(trajectory) - len(recent) + i + 1}: Finished ({status})"
                else:
                    history_context += f"Step {len(trajectory) - len(recent) + i + 1}: {action.get('action', 'unknown')}"
                
                # Add result
                if result.get('success'):
                    history_context += " → Success\n"
                else:
                    history_context += f" → Failed: {result.get('error', 'unknown error')}\n"
            
            # Check for repetitive actions
            if len(recent) >= 2:
                last_action = recent[-1].get('action', {})
                second_last = recent[-2].get('action', {})
                
                if (last_action.get('action') == 'left_click' and 
                    second_last.get('action') == 'left_click' and
                    last_action.get('coordinate') == second_last.get('coordinate')):
                    coord = last_action.get('coordinate')
                    repeat_warning = f"\n**CRITICAL**: You clicked point {coord} twice! Check if task is complete before clicking again."
        
        # Simple instruction for OpenAI computer-use
        return build_operator_prompt(
            task_description=task_description,
            repeat_warning=repeat_warning,
            history_context=(history_context if history_context else "No previous actions"),
            current_step=current_step,
            max_steps=self.max_steps,
        )
    
    async def _get_computer_use_action(self, prompt: str, screenshot: str) -> Dict[str, Any]:
        """Get next Operator action using the documented loop with computer_call_output"""
        
        max_retries = 5
        attempt = 0
        
        while True:
            try:
                attempt += 1
                
                # Initial vs. subsequent loop call
                if not self._last_response_id:
                    response = await self.model_client.call_operator_initial(
                        prompt,
                        screenshot,
                        display_width=self.display_width,
                        display_height=self.display_height,
                        environment='browser'
                    )
                else:
                    response = await self.model_client.call_operator_next(
                        previous_response_id=self._last_response_id,
                        call_id=self._last_call_id,
                        screenshot=screenshot,
                        display_width=self.display_width,
                        display_height=self.display_height,
                        environment='browser'
                    )
                
                if not response:
                    print(f"🔄 {self.cua_model_name} empty response (attempt {attempt}), retrying...")
                    continue
                
                print(f"Raw OpenAI response type: {type(response)}")
                
                # Parse OpenAI computer-use response
                computer_calls = []
                reasoning_text = ""
                reasoning_source = "none"
                
                if hasattr(response, 'output') and response.output:
                    # Prefer reasoning.summary if available
                    reasoning_items = [item for item in response.output if hasattr(item, 'type') and item.type == "reasoning"]
                    if reasoning_items:
                        reasoning = reasoning_items[0]
                        if hasattr(reasoning, 'summary') and reasoning.summary:
                            for summary_item in reasoning.summary:
                                if hasattr(summary_item, 'text') and summary_item.text:
                                    reasoning_text = summary_item.text
                                    reasoning_source = "summary"
                                    break
                    # Fallback: try assistant/message text parts
                    if not reasoning_text:
                        try:
                            for item in response.output:
                                t = getattr(item, 'type', None)
                                content = getattr(item, 'content', None)
                                if t in ("message", "assistant_message") and content:
                                    for part in content:
                                        txt = getattr(part, 'text', None)
                                        if txt:
                                            reasoning_text = txt
                                            reasoning_source = "message"
                                            break
                                if reasoning_text:
                                    break
                        except Exception:
                            pass
                    
                    # Extract computer_call
                    computer_calls = [item for item in response.output if hasattr(item, 'type') and item.type == "computer_call"]
                
                if computer_calls:
                    # Process the first computer_call
                    computer_call = computer_calls[0]
                    action = computer_call.action
                    
                    # Convert OpenAI action to internal format
                    action_dict = self._convert_openai_action_to_internal(action)
                    
                    # Display thought for monitoring
                    if reasoning_text:
                        print(f"     OpenAI reasoning: {reasoning_text[:100]}...")
                    
                    print(f"OpenAI action: {action.type if hasattr(action, 'type') else 'unknown'}")

                    # Maintain loop state
                    if hasattr(response, 'id'):
                        self._last_response_id = response.id
                    if hasattr(computer_call, 'call_id'):
                        self._last_call_id = computer_call.call_id
                    
                    # Serialize raw response for logging
                    raw_json = response.model_dump_json() if hasattr(response, 'model_dump_json') else None
                    return {"action": action_dict, "thought": reasoning_text, "reasoning_source": reasoning_source, "raw": raw_json}
                else:
                    print(f"🔄 No computer_call found in response (attempt {attempt}), retrying...")
                    if attempt >= max_retries:
                        raise RuntimeError("Operator returned no computer_call after retries")
                    continue
                    
            except Exception as e:
                error_msg = str(e)[:50]
                print(f"🔄 {self.cua_model_name} error: {error_msg}... (attempt {attempt}), retrying...")
                if attempt >= max_retries:
                    raise
                continue
    
    def _convert_openai_action_to_internal(self, openai_action) -> Dict[str, Any]:
        """Convert OpenAI computer-use action to internal format"""
        if not hasattr(openai_action, 'type'):
            raise RuntimeError("Operator action missing type")
        
        action_type = openai_action.type
        
        if action_type == "click":
            btn = getattr(openai_action, 'button', None)
            mapped = "right_click" if (isinstance(btn, str) and btn.lower() == "right") else "left_click"
            return {
                "action": mapped,
                "coordinate": [
                    getattr(openai_action, 'x', 0),
                    getattr(openai_action, 'y', 0)
                ]
            }
        
        if action_type in ("double_click", "left_double"):
            return {
                "action": "double_click",
                "coordinate": [getattr(openai_action, 'x', 0), getattr(openai_action, 'y', 0)]
            }

        if action_type in ("right_click", "right_single"):
            return {
                "action": "right_click",
                "coordinate": [getattr(openai_action, 'x', 0), getattr(openai_action, 'y', 0)]
            }

        if action_type in ("move", "mousemove", "pointer_move"):
            return {
                "action": "mouse_move",
                "coordinate": [getattr(openai_action, 'x', 0), getattr(openai_action, 'y', 0)]
            }

        if action_type == "type":
            return {
                "action": "type",
                "text": getattr(openai_action, 'text', '')
            }
        
        if action_type == "scroll":
            # Support both scroll_x/scroll_y and delta_x/delta_y
            scroll_x = getattr(openai_action, 'scroll_x', getattr(openai_action, 'delta_x', 0))
            scroll_y = getattr(openai_action, 'scroll_y', getattr(openai_action, 'delta_y', 0))
            return {
                "action": "scroll",
                "coordinate": [
                    getattr(openai_action, 'x', self.display_width // 2),
                    getattr(openai_action, 'y', self.display_height // 2)
                ],
                "pixels_x": scroll_x,
                "pixels_y": scroll_y
            }
        
        if action_type in ("keypress", "key_press", "keydown", "key_down", "keyup", "key_up", "key"):
            keys = getattr(openai_action, 'keys', None)
            if keys is None:
                single = getattr(openai_action, 'key', None)
                keys = [single] if single else []
            return {"action": "key", "keys": list(keys)}

        if action_type == "wait":
            return {"action": "wait", "time": 2}

        if action_type == "screenshot":
            return {"action": "screenshot"}

        if action_type == "drag":
            fx = getattr(openai_action, 'from_x', getattr(openai_action, 'x', None))
            fy = getattr(openai_action, 'from_y', getattr(openai_action, 'y', None))
            tx = getattr(openai_action, 'to_x', None)
            ty = getattr(openai_action, 'to_y', None)
            if fx is not None and fy is not None and tx is not None and ty is not None:
                return {"action": "drag", "from": [fx, fy], "to": [tx, ty]}
            if tx is not None and ty is not None:
                return {"action": "mouse_move", "coordinate": [tx, ty]}
            raise RuntimeError("Operator drag action missing coordinates")

        raise RuntimeError(f"Unsupported OpenAI action type: {action_type}")
    
    def _convert_parsed_to_internal(self, parsed_action: Dict[str, Any]) -> Dict[str, Any]:
        """Override: OpenAI actions are already converted, just pass through"""
        return parsed_action
