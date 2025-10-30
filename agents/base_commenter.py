import json
import tempfile
import asyncio
from typing import List, Dict, Any, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.browser import BrowserController

# Global browser pool to prevent resource exhaustion
_browser_pool = []
_browser_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent browsers
_pool_lock = asyncio.Lock()

class BaseCommenter(ABC):
    def __init__(self, model_client):
        """分析CUA失败轨迹的UI问题 - 基类"""
        self.model_client = model_client
        # 映射到对应的VLM模型配置
        self.model_mapping = {
            'qwen': 'qwen2.5-vl-72b'
        }
        
    def _get_actual_model_name(self, model_name: str) -> str:
        """获取实际的模型名称"""
        return self.model_mapping.get(model_name, model_name)
    
    async def _safe_capture_screenshot(self, html_content: str, timeout_seconds: int = 30) -> tuple[str, tuple[int, int]]:
        """Safely capture screenshot with timeout; no fallback image on failure"""
        return await asyncio.wait_for(
            self._capture_version_screenshot(html_content), 
            timeout=timeout_seconds
        )
    
    async def _get_browser_from_pool(self):
        """Get browser from pool with strict resource limits"""
        async with _pool_lock:
            if _browser_pool:
                return _browser_pool.pop()
        
        # No available browsers, create new one with semaphore limit
        async with _browser_semaphore:
            browser = BrowserController(headless=True, width=1280, height=1024)
            await browser.start()
            return browser
    
    async def _return_browser_to_pool(self, browser):
        """Return browser to pool or close if pool is full"""
        async with _pool_lock:
            if len(_browser_pool) < 3:  # Keep max 3 browsers in pool
                _browser_pool.append(browser)
            else:
                try:
                    await browser.close()
                except:
                    pass  # Ignore cleanup errors
    
    async def _capture_version_screenshot(self, html_content: str) -> tuple[str, tuple[int, int]]:
        """为HTML版本截图 - 使用浏览器池防止资源耗尽
        
        Returns:
            tuple: (screenshot_base64, (width, height))
        """
        browser = await self._get_browser_from_pool()
        
        try:
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name
            
            # 加载页面
            await browser.navigate_to(f"file://{temp_html_path}")
            await asyncio.sleep(0.5)  # 减少等待时间
            
            # 获取页面实际尺寸
            page_size = await browser.page.evaluate("""() => {
                return {
                    width: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
                    height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
                }
            }""")
            
            # 截图
            screenshot_base64 = await browser.screenshot()
            
            # 清理临时文件
            Path(temp_html_path).unlink()
            
            return screenshot_base64, (page_size['width'], page_size['height'])
            
        finally:
            await self._return_browser_to_pool(browser)
    
    @abstractmethod
    def _prepare_analysis_inputs(self, storyboard_path: str, html_content: str, website_screenshot: str, width: int, height: int) -> tuple[str, List[str]]:
        """准备分析输入 - 子类实现具体逻辑
        
        Returns:
            tuple: (prompt, screenshot_inputs)
        """
        pass
    
    async def analyze_single_failure(self, storyboard_path: str, html_content: str, model_name: str = "gpt5") -> str:
        """分析单个CUA失败轨迹的UI问题
        
        Args:
            storyboard_path: storyboard图片路径
            html_content: 网站HTML内容
            model_name: 用于分析的模型（gpt5, gpt4o, qwen等）
            
        Returns:
            str: 该轨迹失败的UI设计问题分析
        """
        try:
            # 检查storyboard文件是否存在
            if not Path(storyboard_path).exists():
                return "Storyboard image not found - cannot analyze failure"
            
            # 获取网站截图用于对比
            website_screenshot, (width, height) = await self._safe_capture_screenshot(html_content)
            
            # 由子类准备具体的分析输入
            prompt, screenshot_inputs = self._prepare_analysis_inputs(
                storyboard_path, html_content, website_screenshot, width, height
            )
            
            # 使用配置的模型进行分析（通常使用VLM如GPT-5或GPT-4o）
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # 使用指定的模型进行视觉分析
                    actual_model = self._get_actual_model_name(model_name)
                    response = await self.model_client.call_commenter(actual_model, prompt, screenshot_inputs)
                    if response and len(response.strip()) > 30:
                        return response.strip()
                except Exception as e:
                    if attempt == max_retries - 1:
                        return f"Failed to analyze failure after {max_retries} attempts: {str(e)}"
                    await asyncio.sleep(1)  # Brief pause between retries
                    continue
            
            return "Unable to analyze failure - no valid response received"
            
        except Exception as e:
            return f"Error analyzing failure trajectory: {str(e)}"
