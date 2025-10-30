import asyncio
import json
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright

class BrowserController:
    def __init__(self, headless: bool = True, width: int = 1280, height: int = 720):
        """简化的浏览器控制器"""
        self.headless = headless
        self.width = width
        self.height = height
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await self.browser.new_context(
            viewport={'width': self.width, 'height': self.height}
        )
        self.page = await context.new_page()
        
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate_to(self, url: str):
        """导航到指定URL"""
        await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
    
    async def screenshot(self, path: Optional[str] = None, full_page: bool = True) -> str:
        """截图 - 支持全页面或视口截图"""
        if path:
            await self.page.screenshot(path=path, full_page=full_page)
            return path
        else:
            # 返回base64编码的截图
            screenshot_bytes = await self.page.screenshot(full_page=full_page)
            import base64
            return base64.b64encode(screenshot_bytes).decode()
    
    async def viewport_screenshot(self, path: Optional[str] = None) -> str:
        """视口截图 - CUA专用"""
        return await self.screenshot(path, full_page=False)
    
    async def click_at_coordinates(self, x: int, y: int):
        """在指定坐标点击"""
        await self.page.mouse.click(x, y)
        await asyncio.sleep(0.5)
        return {"success": True, "message": "Clicked"}
    
    async def type_text(self, text: str):
        """在当前焦点输入文本"""
        await self.page.keyboard.type(text)
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Typed: {text}"}
    
    async def scroll(self, direction: str = "down"):
        """滚动页面"""
        if direction.lower() == "up":
            await self.page.evaluate("window.scrollBy(0, -500)")
        else:
            await self.page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Scrolled {direction}"}

    async def scroll_by(self, delta_x: int = 0, delta_y: int = 0):
        """按像素精确滚动页面，支持水平和垂直方向"""
        # Use native wheel to avoid evaluate arg mismatch issues
        await self.page.mouse.wheel(delta_x, delta_y)
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Scrolled by dx={delta_x}, dy={delta_y}"}

    async def scroll_to_coordinates(self, x: int, y: int, direction: str = "down", pixels: int = 500):
        """在指定坐标位置滚动"""
        scroll_delta = -pixels if direction.lower() == "up" else pixels
        # Move to anchor, then wheel with deltaY
        await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(0, scroll_delta)
        await asyncio.sleep(0.5)
    
    async def double_click_at_coordinates(self, x: int, y: int):
        """在指定坐标双击"""
        await self.page.mouse.dblclick(x, y)
        await asyncio.sleep(0.5)
        return {"success": True, "message": "Double clicked"}
    
    async def right_click_at_coordinates(self, x: int, y: int):
        """在指定坐标右击"""
        await self.page.mouse.click(x, y, button='right')
        await asyncio.sleep(0.5)
        return {"success": True, "message": "Right clicked"}
    
    async def move_to_coordinates(self, x: int, y: int):
        """移动鼠标到指定坐标"""
        await self.page.mouse.move(x, y)
        await asyncio.sleep(0.5)
        return {"success": True, "message": "Mouse moved"}
    
    def _map_key_name(self, key: str) -> str:
        """Map key names to Playwright-compatible names"""
        key_mapping = {
            # Arrow keys
            'arrowleft': 'ArrowLeft',
            'arrowright': 'ArrowRight', 
            'arrowup': 'ArrowUp',
            'arrowdown': 'ArrowDown',
            'left': 'ArrowLeft',
            'right': 'ArrowRight',
            'up': 'ArrowUp',
            'down': 'ArrowDown',
            # Common keys
            'space': 'Space',
            'enter': 'Enter',
            'return': 'Enter',
            'tab': 'Tab',
            'escape': 'Escape',
            'backspace': 'Backspace',
            'delete': 'Delete',
            'shift': 'Shift',
            'ctrl': 'Control',
            'control': 'Control',
            'alt': 'Alt',
            'meta': 'Meta',
            'cmd': 'Meta',
            'home': 'Home',
            'end': 'End',
            'pageup': 'PageUp',
            'pagedown': 'PageDown',
            'insert': 'Insert'
        }
        # Map function keys f1..f12
        lk = key.lower()
        if lk.startswith('f') and lk[1:].isdigit():
            n = int(lk[1:])
            if 1 <= n <= 12:
                return f"F{n}"
        return key_mapping.get(lk, key)

    async def press_keys(self, keys: list):
        """按下键盘组合键"""
        if not keys:
            return {"success": False, "error": "No keys provided"}
        
        # Map all key names to Playwright-compatible names
        mapped_keys = [self._map_key_name(key) for key in keys]
        
        # 按下所有修饰键
        for key in mapped_keys[:-1]:
            await self.page.keyboard.down(key)
        
        # 按下最后一个键
        await self.page.keyboard.press(mapped_keys[-1])
        
        # 释放修饰键
        for key in reversed(mapped_keys[:-1]):
            await self.page.keyboard.up(key)
        
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Pressed keys: {' + '.join(keys)}"}
    
    async def drag_to_coordinates(self, x: int, y: int):
        """拖拽到指定坐标(需要先有鼠标按下状态)"""
        await self.page.mouse.move(x, y)
        await self.page.mouse.up()
        await asyncio.sleep(0.5)
        return {"success": True, "message": "Dragged to coordinates"}

    async def mouse_down_at(self, x: int, y: int):
        """在指定坐标按下鼠标左键"""
        await self.page.mouse.move(x, y)
        await self.page.mouse.down()
        await asyncio.sleep(0.2)
        return {"success": True, "message": "Mouse down"}

    async def mouse_up(self):
        """释放鼠标左键"""
        await self.page.mouse.up()
        await asyncio.sleep(0.2)
        return {"success": True, "message": "Mouse up"}

    async def drag_from_to(self, x1: int, y1: int, x2: int, y2: int):
        """从(x1,y1)按下并拖拽到(x2,y2)然后释放"""
        await self.page.mouse.move(x1, y1)
        await self.page.mouse.down()
        await self.page.mouse.move(x2, y2)
        await self.page.mouse.up()
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Dragged from ({x1},{y1}) to ({x2},{y2})"}
    
    async def inject_state_monitor_script(self):
        """注入状态监控脚本"""
        script = """
        window.AUIStateMonitor = {
            getState: function() {
                const state = {};
                // Global page context useful for detecting progress
                try {
                    const vv = window.visualViewport || {};
                    const se = document.scrollingElement || document.documentElement || document.body;
                    state.__meta_viewport_width = window.innerWidth;
                    state.__meta_viewport_height = window.innerHeight;
                    state.__meta_device_pixel_ratio = window.devicePixelRatio || 1;
                    state.__meta_visual_scale = vv.scale || 1;
                    state.__meta_scroll_top = se.scrollTop || 0;
                    state.__meta_scroll_height = se.scrollHeight || 0;
                    state.__meta_scroll_left = se.scrollLeft || 0;
                    state.__meta_scroll_width = se.scrollWidth || 0;
                    state.__meta_location_hash = location.hash || '';
                    state.__meta_location_path = location.pathname || '';
                    state.__meta_location_search = location.search || '';
                    state.__meta_document_title = document.title || '';
                    const ae = document.activeElement;
                    state.__meta_active_element_id = (ae && ae.id) ? ae.id : '';
                } catch (e) {}
                
                // 提取所有有ID的元素的文本内容
                const elementsWithId = document.querySelectorAll('[id]');
                elementsWithId.forEach(elem => {
                    if (elem.id) {
                        state[elem.id] = elem.textContent.trim();
                        
                        // 提取输入值
                        if (elem.tagName === 'INPUT' || elem.tagName === 'TEXTAREA' || elem.tagName === 'SELECT') {
                            if (elem.type === 'checkbox' || elem.type === 'radio') {
                                state[elem.id] = elem.checked;
                            } else {
                                state[elem.id] = elem.value;
                            }
                        }
                        
                        // 记录可见性
                        try {
                            const cs = getComputedStyle(elem);
                            state[elem.id + '_visible'] = !elem.hidden && cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0';
                        } catch (e) {
                            state[elem.id + '_visible'] = !elem.hidden;
                        }
                        
                        // 记录class和data-*以捕获状态变化
                        try { state[elem.id + '_class'] = elem.className || ''; } catch (e) {}
                        try { state[elem.id + '_data'] = Object.assign({}, elem.dataset || {}); } catch (e) {}
                        // 记录 aria-* 属性（作为可监测状态）
                        try {
                            const aria = {};
                            if (elem.attributes) {
                                for (let i = 0; i < elem.attributes.length; i++) {
                                    const attr = elem.attributes[i];
                                    if (attr && attr.name && attr.name.startsWith('aria-')) {
                                        aria[attr.name.substring(5)] = attr.value;
                                    }
                                }
                            }
                            state[elem.id + '_aria'] = aria;
                        } catch (e) {}
                        // 记录常见HTML属性用于规则评估（仅选择一小部分以保持简洁）
                        try {
                            const attr = {};
                            const names = ['href','src','download','role','type','value'];
                            for (const n of names) {
                                try {
                                    const v = elem.getAttribute(n);
                                    if (v !== null) attr[n] = v;
                                } catch (e2) {}
                            }
                            state[elem.id + '_attr'] = attr;
                        } catch (e) {}
                    }
                });
                
                // 额外提取没有ID但有重要class的元素
                const importantClasses = ['.result', '.output', '.score', '.status', '.message', 
                                        '.timer', '.color-word', '.color-button'];
                importantClasses.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((elem, index) => {
                        const key = selector.replace('.', '') + (index > 0 ? `_${index}` : '');
                        state[key] = elem.textContent.trim();
                        
                        // 对于输入元素，也提取值
                        if (elem.tagName === 'INPUT' || elem.tagName === 'TEXTAREA' || elem.tagName === 'SELECT') {
                            if (elem.type === 'checkbox' || elem.type === 'radio') {
                                state[key] = elem.checked;
                            } else {
                                state[key] = elem.value;
                            }
                        }
                        // 记录class以捕获部分视觉状态
                        try { state[key + '_class'] = elem.className || ''; } catch (e) {}
                    });
                });
                
                // 提取通用输入值（作为备用）
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach((input, index) => {
                    if (!input.id) {
                        const key = input.name || `input_${index}`;
                        if (input.type === 'checkbox' || input.type === 'radio') {
                            state[key] = input.checked;
                        } else {
                            state[key] = input.value;
                        }
                    }
                });
                
                return state;
            }
        };
        """
        await self.page.evaluate(script)
    
    async def get_page_state(self) -> Dict[str, Any]:
        """获取页面状态"""
        state = await self.page.evaluate("window.AUIStateMonitor.getState()")
        return state
    
    async def get_page_content(self) -> str:
        """获取页面HTML内容"""
        return await self.page.content()
    
    async def get_page_info(self) -> Dict[str, Any]:
        """获取页面基本信息"""
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "ready_state": await self.page.evaluate("document.readyState")
        }
