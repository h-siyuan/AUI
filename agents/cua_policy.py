import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.browser import BrowserController
from utils.action_parser import parse_action_to_structure_output
from .base_cua_policy import BaseCUAPolicy
from .prompts.cua_prompts import build_doubao_prompt

def create_cua_policy(model_client, cua_model_name: str = "uitars", max_steps: int = 10):
    """Factory function to create appropriate CUA policy based on model name"""
    if cua_model_name == "operator":
        from .operator_cua_policy import OperatorCUAPolicy
        return OperatorCUAPolicy(model_client, cua_model_name, max_steps)
    else:
        # Default to UI-TARS style policy
        return CUAPolicy(model_client, cua_model_name, max_steps)

class CUAPolicy(BaseCUAPolicy):
    def __init__(self, model_client, cua_model_name: str = "uitars", max_steps: int = 10):
        """CUA Policy - supports both UI-TARS and operator models"""
        super().__init__(model_client, cua_model_name, max_steps)
        self.cua_model_name = cua_model_name
    
    def _build_computer_use_prompt(self, task_description: str, success_criteria: str, 
                                   trajectory: List[Dict], current_step: int) -> str:
        """Build prompt using ByteDance Doubao format for UI-TARS-1.5-7B"""
        
        # Build action history in Doubao format
        history_text = ""
        repeat_warning = ""
        
        if trajectory:
            recent = trajectory[-5:]  # Show more recent actions for context
            for i, t in enumerate(recent):
                action = t.get('action', {})
                result = t.get('result', {})
                
                # Convert our action format to Doubao's readable format
                if action.get('action') == 'left_click':
                    coord = action.get('coordinate', [])
                    if coord:
                        history_text += f"Action: click(point='<point>{coord[0]} {coord[1]}</point>')"
                elif action.get('action') == 'type':
                    text = action.get('text', '')
                    history_text += f"Action: type(content='{text}')"
                elif action.get('action') == 'scroll':
                    pixels = action.get('pixels', 0)
                    direction = 'down' if pixels < 0 else 'up'
                    history_text += f"Action: scroll(direction='{direction}')"
                elif action.get('action') == 'terminate':
                    status = action.get('status', 'success')
                    history_text += f"Action: finished(content='{status}')"
                else:
                    history_text += f"Action: {action.get('action', 'unknown')}"
                
                # Add result
                if result.get('success'):
                    history_text += " -> Success\n"
                else:
                    history_text += f" -> Failed: {result.get('error', 'unknown error')}\n"
            
            # Check for repetitive actions
            if len(recent) >= 2:
                last_action = recent[-1].get('action', {})
                second_last = recent[-2].get('action', {})
                
                if (last_action.get('action') == 'left_click' and 
                    second_last.get('action') == 'left_click' and
                    last_action.get('coordinate') == second_last.get('coordinate')):
                    coord = last_action.get('coordinate')
                    repeat_warning = f"\n**CRITICAL**: You clicked point {coord} twice! Check if task is complete before clicking again."
        
        # Simple instruction following official Doubao format
        instruction = f"""{task_description}

{repeat_warning}

Action history:
{history_text if history_text else "No previous actions"}

Current step: {current_step}/{self.max_steps}"""

        # Use official ByteDance COMPUTER_USE_DOUBAO prompt
        prompt = build_doubao_prompt(instruction)
        
        return prompt
    
    async def _get_computer_use_action(self, prompt: str, screenshot: str) -> Dict[str, Any]:
        """Get Computer Use action from VLM using Doubao format parsing with retry for parse failures"""
        
        # UI-TARS is a local model, use infinite retry for parse failures
        max_retries = float('inf')
        attempt = 0
        
        while True:
            try:
                attempt += 1
                
                # Call VLM directly with Doubao prompt (no function calling needed)
                # model_client.call_model already has infinite retry for local models
                response = await self.model_client.call_cua_model(
                    self.cua_model_name,
                    prompt,
                    images=[screenshot]
                )
                
                if not response:
                    print(f"🔄 {self.cua_model_name} empty response (attempt {attempt}), retrying...")
                    continue
                
                # Parse Doubao format response
                content = response
                print(f"Raw VLM response: {content[:200]}...")
                
                # Extract both Thought and Action lines from UI-TARS format
                thought_line = ""
                action_line = ""
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('Thought:'):
                        thought_line = line[8:].strip()  # Remove "Thought: " prefix
                    elif line.startswith('Action:'):
                        action_line = line[7:].strip()  # Remove "Action: " prefix
                
                if not action_line:
                    print(f"🔄 No Action line found in response (attempt {attempt}), retrying...")
                    continue
                
                # Display thought for monitoring
                if thought_line:
                    print(f"     Model thought: {thought_line[:100]}...")
                
                print(f"Extracted action: {action_line}")
                
                # Use utils action_parser to parse UI-TARS output
                # parse_action_to_structure_output expects full text with Thought: and Action:
                parsed_actions = parse_action_to_structure_output(
                    text=content,
                    factor=28,  # UI-TARS-1.5 uses IMAGE_FACTOR=28 for smart_resize
                    origin_resized_height=self.display_height,
                    origin_resized_width=self.display_width,
                    model_type="qwen25vl"
                )
                
                if parsed_actions and len(parsed_actions) > 0:
                    # Convert first parsed action to our format
                    first_action = parsed_actions[0]
                    action_dict = self._convert_parsed_to_internal(first_action)
                    # Return both action and thought
                    return {"action": action_dict, "thought": thought_line}
                else:
                    print(f"🔄 No actions parsed from response (attempt {attempt}), retrying...")
                    continue
                    
            except Exception as e:
                error_msg = str(e)[:50]
                print(f"🔄 {self.cua_model_name} error: {error_msg}... (attempt {attempt}), retrying...")
                continue

    
