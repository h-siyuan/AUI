"""
Storyboard Generator for CUA Failure Analysis

Generates single storyboard images from CUA trajectory data.
Layout: 5x2 grid (2 rows, 5 columns) with task info at top.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import os
from .logging_utils import ts_print

class StoryboardGenerator:
    """Generate storyboard images from CUA failure trajectories"""
    
    def __init__(self):
        # Canvas constraints: 1920x1080 maximum size
        self.max_canvas_width = 1920
        self.max_canvas_height = 1080
        
        # Target aspect ratio for individual screenshots
        self.target_ratio = 16 / 9
        
        # Fixed spacing and header sizing
        self.header_height = 120             # Header for task info
        self.text_height = 75                # Text area below each screenshot
        self.margin = 12                     # Margin between elements
        self.line_height = 22                # Line height for 18pt font in header
        self.action_line_height = 22         # Line height for 18pt action labels
        
        # Use Times fonts for better readability
        try:
            self.font_bold = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 18)  # Bold for labels (Action:, Thought:) - same size as regular
            self.font_regular = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 18)  # Regular for content
            self.font_header = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 30) # Keep for compatibility (not used)
        except:
            self.font_bold = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
    
    def _calculate_optimal_grid(self, num_screenshots: int) -> tuple[int, int, int, int, int, int]:
        """
        Calculate optimal grid layout and dimensions for a positive number of screenshots.
        Requires num_screenshots >= 1 (caller ensures non-empty screenshots).
        Returns: (grid_cols, grid_rows, screenshot_width, screenshot_height, total_width, total_height)
        """
        
        # Try different grid layouts to find optimal fit within canvas
        best_layout = None
        best_screenshot_size = 0
        
        # Test various grid configurations
        for cols in range(1, min(num_screenshots + 1, 10)):  # Max 10 columns
            rows = (num_screenshots + cols - 1) // cols  # Ceiling division
            if rows > 6:  # Max 6 rows for readability
                continue
            
            # Calculate available space for this grid
            available_width = self.max_canvas_width - (self.margin * (cols - 1))
            available_height = self.max_canvas_height - self.header_height - (self.margin * (rows - 1)) - (self.text_height * rows)
            
            # Calculate max screenshot size per grid cell
            max_screenshot_width = available_width // cols
            max_screenshot_height = available_height // rows
            
            # Choose size based on aspect ratio constraint
            if max_screenshot_width / max_screenshot_height > self.target_ratio:
                screenshot_height = max_screenshot_height
                screenshot_width = int(screenshot_height * self.target_ratio)
            else:
                screenshot_width = max_screenshot_width
                screenshot_height = int(screenshot_width / self.target_ratio)
            
            # Check minimum size requirements
            if screenshot_width < 50 or screenshot_height < 28:
                continue
            
            # Calculate total dimensions
            total_width = (screenshot_width + self.margin) * cols - self.margin
            total_height = self.header_height + (screenshot_height + self.text_height + self.margin) * rows - self.margin
            
            # Check if fits within canvas
            if total_width <= self.max_canvas_width and total_height <= self.max_canvas_height:
                screenshot_area = screenshot_width * screenshot_height
                if screenshot_area > best_screenshot_size:
                    best_screenshot_size = screenshot_area
                    best_layout = (cols, rows, screenshot_width, screenshot_height, total_width, total_height)
        
        # If no layout fits, scale layout to fit canvas
        if not best_layout:
            # Use 5x2 as default and scale down
            cols, rows = 5, 2
            if num_screenshots > 10:
                cols = min(5, num_screenshots)
                rows = (num_screenshots + cols - 1) // cols
            
            # Calculate with scaling
            available_width = self.max_canvas_width - (self.margin * (cols - 1))
            available_height = self.max_canvas_height - self.header_height - (self.margin * (rows - 1)) - (self.text_height * rows)
            
            max_screenshot_width = available_width // cols
            max_screenshot_height = available_height // rows
            
            if max_screenshot_width / max_screenshot_height > self.target_ratio:
                screenshot_height = max_screenshot_height
                screenshot_width = int(screenshot_height * self.target_ratio)
            else:
                screenshot_width = max_screenshot_width
                screenshot_height = int(screenshot_width / self.target_ratio)
            
            total_width = (screenshot_width + self.margin) * cols - self.margin
            total_height = self.header_height + (screenshot_height + self.text_height + self.margin) * rows - self.margin
            
            # Scale down if needed
            if total_width > self.max_canvas_width or total_height > self.max_canvas_height:
                width_scale = self.max_canvas_width / total_width if total_width > self.max_canvas_width else 1.0
                height_scale = self.max_canvas_height / total_height if total_height > self.max_canvas_height else 1.0
                scale = min(width_scale, height_scale)
                
                screenshot_width = int(screenshot_width * scale)
                screenshot_height = int(screenshot_height * scale)
                total_width = int(total_width * scale)
                total_height = int(total_height * scale)
            
            best_layout = (cols, rows, screenshot_width, screenshot_height, total_width, total_height)
        
        return best_layout
    
    async def generate_storyboard(self, app_name: str, model_name: str, task_index: int, 
                                task_description: str, expected_outcome: str,
                                trajectory_dir: Path, v0_dir: str = None) -> Optional[str]:
        """
        Generate storyboard image for a single failed trajectory
        
        Args:
            app_name: Application name
            model_name: Model name
            task_index: Task index (1-based)
            task_description: Task description text
            expected_outcome: Expected outcome text  
            trajectory_dir: Directory containing trajectory screenshots and data
            v0_dir: Initial data directory name
            
        Returns:
            Path to generated storyboard image, or None if failed
        """
        try:
            # Load trajectory metadata (may be empty for short/stuck runs)
            trajectory_data = await self._load_trajectory_data(trajectory_dir)
            actual_steps = len(trajectory_data) if trajectory_data else 0
            
            # Collect screenshots
            screenshot_files: List[Path] = []
            if actual_steps > 0:
                # Use step count from trajectory.json
                for step in range(1, actual_steps + 1):
                    step_file = trajectory_dir / f"step_{step}.png"
                    if step_file.exists():
                        screenshot_files.append(step_file)
            
            if not screenshot_files:
                # Use on-disk images when trajectory.json is missing or empty
                # This uses available visual evidence alongside generated artifacts
                screenshot_files = sorted(trajectory_dir.glob('step_*.png'))
                # Exclude step_0.png if present
                screenshot_files = [p for p in screenshot_files if not p.name.startswith('step_0')]
                if screenshot_files and not trajectory_data:
                    # Create empty action entries to match screenshots length
                    trajectory_data = [{} for _ in screenshot_files]
                    actual_steps = len(trajectory_data)
            
            if not screenshot_files:
                return None
            
            # Calculate optimal grid layout for actual screenshot count
            grid_cols, grid_rows, screenshot_width, screenshot_height, total_width, total_height = self._calculate_optimal_grid(len(screenshot_files))
            
            # Set dynamic grid parameters
            self.grid_cols = grid_cols
            self.grid_rows = grid_rows
            self.screenshot_width = screenshot_width
            self.screenshot_height = screenshot_height
            self.total_width = total_width
            self.total_height = total_height
            
            # Calculate action circle radius based on screenshot size
            scale_factor = self.screenshot_width / 1280
            self.action_circle_radius = max(15, int(25 * scale_factor))
            
            # Create storyboard image
            storyboard = Image.new('RGB', (self.total_width, self.total_height), 'white')
            draw = ImageDraw.Draw(storyboard)
            
            # Draw header with task info
            self._draw_header(draw, task_description, expected_outcome)
            
            # Draw 5x2 grid of screenshots with actions
            await self._draw_screenshot_grid(storyboard, draw, screenshot_files, trajectory_data)
            
            # Yield to event loop before saving to keep UI responsive
            await asyncio.sleep(0)
            
            # Save storyboard
            storyboard_path = trajectory_dir / "storyboard.png"
            storyboard.save(str(storyboard_path))
            
            return str(storyboard_path)
            
        except Exception as e:
            import traceback
            ts_print(f"Failed to generate storyboard for {app_name}/{model_name}/task_{task_index}: {e}")
            ts_print(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def _load_trajectory_data(self, trajectory_dir: Path) -> List[Dict[str, Any]]:
        """Load trajectory action/reasoning data from trajectory.json"""
        trajectory_file = trajectory_dir / "trajectory.json"
        if trajectory_file.exists():
            try:
                with open(trajectory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                ts_print(f"Failed to load trajectory data: {e}")
                return []
        return []
    
    def _draw_header(self, draw: ImageDraw, task_description: str, expected_outcome: str):
        """Draw header section with task description and expected outcome (same as paper figure)"""
        y_pos = self.margin
        
        # Draw Task label in bold, content in regular (no Result on same line)
        draw.text((self.margin, y_pos), "Task:", font=self.font_bold, fill='black')
        bbox = self.font_bold.getbbox("Task:")
        task_content_x = self.margin + bbox[2] - bbox[0] + 5
        
        task_lines = self._wrap_text(task_description, self.font_regular, self.total_width - task_content_x - self.margin)
        draw.text((task_content_x, y_pos), task_lines[0] if task_lines else "", font=self.font_regular, fill='black')
        y_pos += self.line_height
        
        # Continue task on next line if needed
        if len(task_lines) > 1:
            draw.text((self.margin, y_pos), task_lines[1], font=self.font_regular, fill='black')
            y_pos += self.line_height
        
        y_pos += 10  # Small gap before Result
        
        # Draw Result: Failure between Task and Expected (Result: in bold, Failure in regular)
        draw.text((self.margin, y_pos), "Result:", font=self.font_bold, fill='black')
        result_bbox = self.font_bold.getbbox("Result:")
        result_content_x = self.margin + result_bbox[2] - result_bbox[0] + 5
        draw.text((result_content_x, y_pos), "Failure", font=self.font_regular, fill='black')
        y_pos += self.line_height
        
        y_pos += 10  # Small gap before Expected
        
        # Draw Expected label in bold, content in regular
        draw.text((self.margin, y_pos), "Expected:", font=self.font_bold, fill='black')
        bbox = self.font_bold.getbbox("Expected:")
        expected_content_x = self.margin + bbox[2] - bbox[0] + 5
        expected_lines = self._wrap_text(expected_outcome, self.font_regular, self.total_width - expected_content_x - self.margin)
        draw.text((expected_content_x, y_pos), expected_lines[0] if expected_lines else "", font=self.font_regular, fill='black')
        y_pos += self.line_height
        
        # Continue expected on next line if needed
        if len(expected_lines) > 1:
            draw.text((self.margin, y_pos), expected_lines[1], font=self.font_regular, fill='black')
            y_pos += self.line_height
    
    def _crop_viewport_screenshot_with_action(self, image: Image, action_coord: tuple = None) -> tuple:
        """Crop viewport screenshot with action-aware positioning (skip 16:9 enforcement since already 16:9)"""
        width, height = image.size
        
        # Dynamic crop factor based on available screenshot size
        # Use larger crops when canvas allows for bigger screenshots
        base_crop_factor = 0.6 if self.screenshot_width > 300 else 0.5
        
        # Calculate base crop dimensions to match target screenshot size
        # Aim to crop to a size that when scaled down fits our screenshot dimensions
        target_crop_width = min(width, int(self.screenshot_width * 2))  # Allow 2x scaling down
        target_crop_height = min(height, int(self.screenshot_height * 2))
        
        # Apply minimum crop factor for consistency
        crop_width = max(target_crop_width, int(width * base_crop_factor))
        crop_height = max(target_crop_height, int(height * base_crop_factor))
        
        # Ensure crop doesn't exceed image bounds
        crop_width = min(crop_width, width)
        crop_height = min(crop_height, height)
        
        # Default center crop
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        
        # Adjust crop area if action coordinate is provided and outside current crop
        if action_coord:
            action_x, action_y = action_coord
            
            # Check if action is outside current crop area
            if action_x < left or action_x > left + crop_width or action_y < top or action_y > top + crop_height:
                # Move crop to center on action, but keep within image bounds
                new_left = max(0, min(width - crop_width, action_x - crop_width // 2))
                new_top = max(0, min(height - crop_height, action_y - crop_height // 2))
                left, top = new_left, new_top
        
        crop_info = {
            'left': left,
            'top': top,
            'width': crop_width,
            'height': crop_height
        }
        
        cropped_image = image.crop((left, top, left + crop_width, top + crop_height))
        return cropped_image, crop_info

    def _draw_action_annotation_with_crop_info(self, draw: ImageDraw, screen_x: int, screen_y: int,
                                             screen_width: int, screen_height: int, action_data: Dict,
                                             original_size: Tuple[int, int], crop_info: Dict, step_number: int):
        """Draw action annotation using crop info for accurate positioning"""
        action_type = action_data.get('action', '')
        
        if action_type in ['left_click', 'right_click'] and 'coordinate' in action_data:
            coord = action_data['coordinate']
            if len(coord) >= 2:
                action_x, action_y = coord[0], coord[1]
                
                # Convert original coordinates to crop coordinates using crop_info
                crop_x = action_x - crop_info['left']
                crop_y = action_y - crop_info['top']
                
                # Check if coordinates are within crop area
                if 0 <= crop_x <= crop_info['width'] and 0 <= crop_y <= crop_info['height']:
                    # Scale to screenshot size
                    scaled_x = int((crop_x / crop_info['width']) * screen_width)
                    scaled_y = int((crop_y / crop_info['height']) * screen_height)
                    
                    # Draw click annotation
                    center_x = screen_x + scaled_x
                    center_y = screen_y + scaled_y
                    
                    # Draw circle
                    draw.ellipse([
                        center_x - self.action_circle_radius,
                        center_y - self.action_circle_radius,
                        center_x + self.action_circle_radius,
                        center_y + self.action_circle_radius
                    ], outline='red', fill='rgba(255,0,0,100)', width=3)
                    
                    # Draw step number
                    draw.text((center_x - 8, center_y - 10), str(step_number),
                             font=self.font_regular, fill='white')
                else:
                    ts_print(f"Warning: Action coordinate ({action_x}, {action_y}) is outside crop area for step {step_number}")

    def _draw_formatted_action_text(self, draw: ImageDraw, x: int, y: int, text: str, max_width: int):
        """Draw action text with bold formatting for step number, Action:, and Thought:"""
        import re
        
        # Parse the text to identify bold parts
        # Format: "1. Action: Click(456,348), Thought: I noticed..."
        match = re.match(r'(\d+\. Action:)\s*(.*?),\s*(Thought:)\s*(.*)', text)
        
        if match:
            step_action_label = match.group(1)  # "1. Action:"
            action_content = match.group(2)     # "Click(456,348)"
            thought_label = match.group(3)      # "Thought:"
            thought_content = match.group(4)    # "I noticed..."
            
            current_x = x
            current_y = y
            
            # Draw step and action label in bold, content in regular
            draw.text((current_x, current_y), step_action_label, font=self.font_bold, fill='black')
            bbox = self.font_bold.getbbox(step_action_label)
            current_x += bbox[2] - bbox[0] + 5
            
            # Draw action content in regular font (no line break)
            draw.text((current_x, current_y), action_content, font=self.font_regular, fill='black')
            action_bbox = self.font_regular.getbbox(action_content)
            current_x += action_bbox[2] - action_bbox[0] + 10
            
            # Draw thought label in bold (no line break)
            draw.text((current_x, current_y), thought_label, font=self.font_bold, fill='black')
            bbox = self.font_bold.getbbox(thought_label)
            current_x += bbox[2] - bbox[0] + 5
            
            # Draw thought content directly after Thought: (let it flow naturally)
            remaining_width = max_width - (current_x - x)
            
            # Check if entire thought fits on current line
            thought_width = self.font_regular.getbbox(thought_content)[2]
            if thought_width <= remaining_width - 10:
                # Entire thought fits on same line
                draw.text((current_x, current_y), thought_content, font=self.font_regular, fill='black')
            else:
                # Need to wrap - draw what fits on current line, then continue below
                words = thought_content.split()
                current_line_text = ""
                remaining_words = []
                
                # Find how many words fit on current line
                for i, word in enumerate(words):
                    test_text = (current_line_text + " " + word).strip()
                    test_width = self.font_regular.getbbox(test_text)[2]
                    if test_width <= remaining_width - 10:
                        current_line_text = test_text
                    else:
                        remaining_words = words[i:]
                        break
                
                # Draw current line
                if current_line_text:
                    draw.text((current_x, current_y), current_line_text, font=self.font_regular, fill='black')
                
                # Draw remaining words on next lines
                if remaining_words:
                    remaining_text = " ".join(remaining_words)
                    remaining_lines = self._wrap_text(remaining_text, self.font_regular, max_width - 20)
                    for line in remaining_lines[:2]:  # Up to 2 more lines
                        current_y += self.action_line_height
                        draw.text((x, current_y), line, font=self.font_regular, fill='black')
        else:
            # Fallback: draw as regular text
            lines = self._wrap_text(text, self.font_regular, max_width)
            for i, line in enumerate(lines[:3]):  # Allow up to 3 lines
                draw.text((x, y + i * self.action_line_height), line, font=self.font_regular, fill='black')

    async def _draw_screenshot_grid(self, storyboard: Image, draw: ImageDraw, 
                                  screenshot_files: List[Path], trajectory_data: Dict):
        """Draw dynamic grid of screenshots with improved cropping and text formatting"""
        start_y = self.header_height
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                step_idx = row * self.grid_cols + col
                if step_idx >= len(screenshot_files):
                    break
                
                # Calculate position
                x = col * (self.screenshot_width + self.margin)
                y = start_y + row * (self.screenshot_height + self.text_height + self.margin)
                
                # Load screenshot (viewport screenshots are already 16:9)
                try:
                    original_screenshot = Image.open(screenshot_files[step_idx])
                    
                    # Get action data for coordinate tracking (no cropping needed for viewport screenshots)
                    action_coord = None
                    if step_idx < len(trajectory_data):
                        action_data = trajectory_data[step_idx].get('action', {})
                        if action_data.get('action') in ['left_click', 'right_click'] and 'coordinate' in action_data:
                            coord = action_data['coordinate']
                            if len(coord) >= 2:
                                action_coord = (coord[0], coord[1])
                    
                    cropped_screenshot, crop_info = self._crop_viewport_screenshot_with_action(original_screenshot, action_coord)
                    
                    # Resize to fixed size to maintain consistent layout
                    if cropped_screenshot.size != (self.screenshot_width, self.screenshot_height):
                        cropped_screenshot = cropped_screenshot.resize((self.screenshot_width, self.screenshot_height), Image.LANCZOS)
                    
                    actual_width, actual_height = self.screenshot_width, self.screenshot_height
                    
                    # Paste screenshot at fixed size
                    storyboard.paste(cropped_screenshot, (x, y))
                    
                    # Draw action annotation with crop info using fixed size
                    if step_idx < len(trajectory_data):
                        action_data = trajectory_data[step_idx].get('action', {})
                        self._draw_action_annotation_with_crop_info(
                            draw, x, y, actual_width, actual_height,
                            action_data, original_screenshot.size, crop_info, step_idx + 1
                        )
                    
                    # Draw action text below screenshot using actual screenshot size
                    text_y = y + actual_height + 5
                    action_text = self._get_step_text(step_idx, trajectory_data)
                    
                    # Draw white background for text (adjust for actual width and action font)
                    text_bg_height = 3 * self.action_line_height + 10  # Space for 3 lines
                    draw.rectangle([x, text_y - 3, x + actual_width, text_y + text_bg_height], 
                                 fill='white', outline='gray')
                    
                    # Draw formatted text with bold elements
                    self._draw_formatted_action_text(draw, x + 3, text_y, action_text, actual_width - 20)
                    # Cooperative yield after each screenshot to avoid blocking the loop
                    await asyncio.sleep(0)

                except Exception as e:
                    # Draw error placeholder
                    draw.rectangle([x, y, x + self.screenshot_width, y + self.screenshot_height],
                                 fill='lightgray', outline='gray', width=2)
                    draw.text((x + 10, y + 10), f"Step {step_idx + 1}\nError loading image",
                             font=self.font_regular, fill='red')
                    # Yield even on error to keep UI responsive
                    await asyncio.sleep(0)

            # Yield after each row
            await asyncio.sleep(0)
    
    def _get_step_text(self, step_idx: int, trajectory_data: List[Dict]) -> str:
        """Get action and reasoning text for a step with step number"""
        if step_idx < len(trajectory_data):
            step = trajectory_data[step_idx]
            action = step.get('action', {})
            thought = step.get('thought', '')
            
            # Format action
            action_type = action.get('action', 'unknown')
            if action_type == 'left_click':
                coord = action.get('coordinate', [])
                action_text = f"Click({coord[0]},{coord[1]})" if coord else "Click"
            elif action_type == 'type':
                text = action.get('text', '')[:20]
                action_text = f"Type: {text}"
            elif action_type == 'scroll':
                action_text = "Scroll"
            elif action_type == 'terminate':
                action_text = "Finish"
            else:
                action_text = action_type
            
            # Format with step number and bold headers
            step_num = step_idx + 1
            thought_text = thought if thought else "No thought"
            return f"{step_num}. Action: {action_text}, Thought: {thought_text}"
        else:
            return f"Step {step_idx + 1}"
    
    def _truncate_text_to_width(self, text: str, font: ImageFont, max_width: int) -> str:
        """Truncate text to fit within max_width, adding ... if needed"""
        if font.getbbox(text)[2] <= max_width:
            return text
        
        # Binary search to find maximum text that fits
        left, right = 0, len(text)
        best_text = ""
        
        while left <= right:
            mid = (left + right) // 2
            test_text = text[:mid] + "..."
            text_width = font.getbbox(test_text)[2]
            
            if text_width <= max_width:
                best_text = test_text
                left = mid + 1
            else:
                right = mid - 1
        
        return best_text if best_text else text[:1] + "..."
    
    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
            except:
                # Fallback for older PIL versions
                text_width = font.getsize(test_line)[0]
                
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Single word too long
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

# Utility function for external use
async def generate_failure_storyboard(app_name: str, model_name: str, task_index: int,
                                    task_description: str, expected_outcome: str, 
                                    trajectory_dir: Path, v0_dir: str = None) -> Optional[str]:
    """
    Generate storyboard for a failed trajectory
    
    Returns:
        Path to storyboard image or None if generation failed
    """
    generator = StoryboardGenerator()
    return await generator.generate_storyboard(
        app_name=app_name,
        model_name=model_name, 
        task_index=task_index,
        task_description=task_description,
        expected_outcome=expected_outcome,
        trajectory_dir=trajectory_dir,
        v0_dir=v0_dir
    )
from .logging_utils import ts_print
