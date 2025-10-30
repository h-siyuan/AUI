import base64
import json
from typing import List, Tuple
from pathlib import Path

from .base_commenter import BaseCommenter
from .prompts.commenter_prompts import build_screenshot_only_prompt

class CommenterScreenshotOnly(BaseCommenter):
    def _load_step_screenshots(self, trajectory_dir: str) -> List[str]:
        """从trajectory目录加载实际步数的step截图（基于trajectory.json）"""
        trajectory_path = Path(trajectory_dir)
        step_screenshots = []
        
        # 首先读取trajectory.json获取实际步数
        trajectory_file = trajectory_path / "trajectory.json"
        actual_steps = 0
        if trajectory_file.exists():
            try:
                with open(trajectory_file, 'r', encoding='utf-8') as f:
                    trajectory_data = json.load(f)
                actual_steps = len(trajectory_data)
            except Exception:
                pass
        
        # 如果没有trajectory.json，回退到检查实际存在的文件
        if actual_steps == 0:
            for step_num in range(1, 21):  # 检查最多20步
                step_file = trajectory_path / f"step_{step_num}.png"
                if step_file.exists():
                    actual_steps = step_num
                else:
                    break
        
        # 加载实际存在的step截图，从step_1开始（跳过step_0）
        for step_num in range(1, actual_steps + 1):
            step_file = trajectory_path / f"step_{step_num}.png"
            if step_file.exists():
                with open(step_file, 'rb') as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode('utf-8')
                    step_screenshots.append(screenshot_base64)
        
        return step_screenshots
    
    def _prepare_analysis_inputs(self, storyboard_path: str, html_content: str, website_screenshot: str, width: int, height: int) -> Tuple[str, List[str]]:
        """准备分析输入 - 使用原始step截图"""
        # 从storyboard路径推导trajectory目录
        storyboard_path_obj = Path(storyboard_path)
        trajectory_dir = storyboard_path_obj.parent
        
        # 加载实际步数的step截图
        step_screenshots = self._load_step_screenshots(str(trajectory_dir))
        
        # 过滤掉空的截图
        valid_screenshots = [s for s in step_screenshots if s]
        if not valid_screenshots:
            raise ValueError("No valid step screenshots found")
        
        # 构建分析prompt（要求结构化JSON输出）
        prompt = build_screenshot_only_prompt(width, height, len(valid_screenshots))

        return prompt, [website_screenshot] + valid_screenshots
