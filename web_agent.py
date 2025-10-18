# web_agent.py - Optimized for MSI Thin 15 B13UC
from __future__ import annotations

import asyncio
import logging
import psutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger("AI_Assistant.WebAgent")

# Lazy imports - only load when needed
_playwright = None
_playwright_browser = None
_browser_context = None
_last_activity = None


class WebAgent:
    """
    Web automation agent optimized for MSI Thin 15 B13UC.
    Features lazy loading, auto-cleanup, and hardware-aware resource management.
    """
    
    def __init__(self):
        # Detect system resources
        self.total_ram_gb = psutil.virtual_memory().total / (1024**3)
        self.cpu_count = psutil.cpu_count()
        
        # Auto-configure based on RAM
        if self.total_ram_gb < 12:
            self.mode = "lightweight"
            self.max_memory_mb = 300
            self.max_concurrent = 1
            self.vision_enabled = False
            logger.info("🔋 Detected 8GB RAM - Using LIGHTWEIGHT mode")
        else:
            self.mode = "balanced"
            self.max_memory_mb = 600
            self.max_concurrent = 2
            self.vision_enabled = True
            logger.info("⚡ Detected 16GB RAM - Using BALANCED mode")
        
        # Browser settings
        self.browser_type = "chromium"
        self.headless = True
        self.auto_close_timeout = 300  # 5 minutes
        
        # State
        self.is_initialized = False
        self.active_tasks = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "tasks_completed": 0,
            "memory_peak_mb": 0,
            "last_task_duration": 0,
            "total_runtime": 0
        }
    
    async def initialize(self) -> bool:
        """
        Lazy initialization - only loads browser when first needed.
        MSI Thin 15 optimized: Uses hardware acceleration on RTX 3050.
        """
        global _playwright, _playwright_browser, _browser_context, _last_activity
        
        if self.is_initialized:
            _last_activity = time.time()
            return True
        
        try:
            # Check available memory before starting
            available_mb = psutil.virtual_memory().available / (1024**2)
            if available_mb < 500:
                logger.warning("⚠️ Low memory (%.0f MB) - skipping web agent", available_mb)
                return False
            
            logger.info("🌐 Initializing web agent (first use)...")
            start_time = time.time()
            
            # Import Playwright (lazy)
            from playwright.async_api import async_playwright
            
            _playwright = await async_playwright().start()
            
            # Browser launch args optimized for MSI Thin 15
            launch_args = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu" if self.total_ram_gb < 12 else "--enable-gpu-rasterization",
                    "--disable-software-rasterizer" if self.total_ram_gb >= 12 else "",
                    f"--window-size=1920,1080",
                    "--disable-blink-features=AutomationControlled",
                ],
            }
            
            # Remove empty args
            launch_args["args"] = [arg for arg in launch_args["args"] if arg]
            
            # Launch browser
            if self.browser_type == "chromium":
                _playwright_browser = await _playwright.chromium.launch(**launch_args)
            elif self.browser_type == "firefox":
                _playwright_browser = await _playwright.firefox.launch(**launch_args)
            else:
                _playwright_browser = await _playwright.webkit.launch(**launch_args)
            
            # Create persistent context
            _browser_context = await _playwright_browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            _last_activity = time.time()
            self.is_initialized = True
            
            # Start auto-cleanup task
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            
            init_time = time.time() - start_time
            logger.info("✅ Web agent ready (%.1fs)", init_time)
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize web agent: %s", e)
            return False
    
    async def close(self) -> None:
        """Gracefully close browser and free resources."""
        global _playwright, _playwright_browser, _browser_context
        
        if not self.is_initialized:
            return
        
        try:
            logger.info("🛑 Closing web agent...")
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if _browser_context:
                await _browser_context.close()
                _browser_context = None
            
            if _playwright_browser:
                await _playwright_browser.close()
                _playwright_browser = None
            
            if _playwright:
                await _playwright.stop()
                _playwright = None
            
            self.is_initialized = False
            logger.info("✅ Web agent closed, memory freed")
            
        except Exception as e:
            logger.error("Error closing web agent: %s", e)
    
    async def _auto_cleanup_loop(self) -> None:
        """Auto-close browser after idle timeout to save RAM."""
        global _last_activity
        
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if _last_activity and self.is_initialized:
                    idle_time = time.time() - _last_activity
                    
                    if idle_time > self.auto_close_timeout and self.active_tasks == 0:
                        logger.info("⏰ Idle timeout - auto-closing browser (saved ~%d MB)", 
                                  self._get_memory_usage())
                        await self.close()
                        break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Auto-cleanup error: %s", e)
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return int(process.memory_info().rss / (1024**2))
    
    def _check_resources(self) -> bool:
        """Check if system has enough resources."""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        if mem.percent > 85:
            logger.warning("⚠️ Memory usage high (%.0f%%) - task may be slow", mem.percent)
            return False
        
        if cpu > 80:
            logger.warning("⚠️ CPU usage high (%.0f%%) - task may be slow", cpu)
            return False
        
        return True
    
    async def navigate(self, url: str) -> Optional[Any]:
        """
        Navigate to URL and return page object.
        Optimized for MSI Thin 15: Monitors resources during navigation.
        """
        global _browser_context, _last_activity
        
        if not await self.initialize():
            return None
        
        if not self._check_resources():
            logger.warning("Skipping navigation due to resource constraints")
            return None
        
        try:
            self.active_tasks += 1
            _last_activity = time.time()
            
            page = await _browser_context.new_page()
            
            logger.info("🌐 Navigating to: %s", url)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            return page
            
        except Exception as e:
            logger.error("Navigation failed: %s", e)
            return None
        finally:
            self.active_tasks -= 1
    
    async def search_amazon(self, query: str) -> Dict[str, Any]:
        """
        Search Amazon for products.
        MSI Thin 15 optimized: Lightweight extraction without heavy vision AI.
        """
        page = await self.navigate(f"https://www.amazon.com/s?k={query}")
        if not page:
            return {"error": "Failed to load Amazon"}
        
        try:
            # Wait for results
            await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
            
            # Extract products (limit to 5 for performance)
            products = []
            items = await page.query_selector_all('[data-component-type="s-search-result"]')
            
            for item in items[:5]:
                try:
                    title_elem = await item.query_selector('h2 a span')
                    price_elem = await item.query_selector('.a-price-whole')
                    
                    if title_elem and price_elem:
                        title = await title_elem.inner_text()
                        price = await price_elem.inner_text()
                        products.append({"title": title.strip(), "price": f"${price.strip()}"})
                except:
                    continue
            
            await page.close()
            self.stats["tasks_completed"] += 1
            
            return {"products": products, "count": len(products)}
            
        except Exception as e:
            logger.error("Amazon search failed: %s", e)
            await page.close()
            return {"error": str(e)}
    
    async def google_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform Google search and extract results.
        Lightweight: Text extraction only, no screenshots.
        """
        page = await self.navigate(f"https://www.google.com/search?q={query}")
        if not page:
            return []
        
        try:
            # Wait for results
            await page.wait_for_selector('#search', timeout=10000)
            
            results = []
            search_results = await page.query_selector_all('.g')
            
            for result in search_results[:num_results]:
                try:
                    title_elem = await result.query_selector('h3')
                    link_elem = await result.query_selector('a')
                    snippet_elem = await result.query_selector('.VwiC3b')
                    
                    if title_elem and link_elem:
                        title = await title_elem.inner_text()
                        link = await link_elem.get_attribute('href')
                        snippet = await snippet_elem.inner_text() if snippet_elem else ""
                        
                        results.append({
                            "title": title.strip(),
                            "url": link,
                            "snippet": snippet.strip()
                        })
                except:
                    continue
            
            await page.close()
            self.stats["tasks_completed"] += 1
            
            return results
            
        except Exception as e:
            logger.error("Google search failed: %s", e)
            await page.close()
            return []
    
    async def fill_form(self, url: str, form_data: Dict[str, str]) -> bool:
        """
        Navigate to page and fill form fields.
        Simple and efficient for MSI Thin 15.
        """
        page = await self.navigate(url)
        if not page:
            return False
        
        try:
            for field_name, value in form_data.items():
                # Try multiple selectors
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'#field_name',
                ]
                
                filled = False
                for selector in selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            await elem.fill(value)
                            filled = True
                            break
                    except:
                        continue
                
                if not filled:
                    logger.warning(f"Could not find field: {field_name}")
            
            await page.close()
            self.stats["tasks_completed"] += 1
            return True
            
        except Exception as e:
            logger.error("Form filling failed: %s", e)
            await page.close()
            return False
    
    async def take_screenshot(self, url: str, path: Optional[str] = None) -> Optional[str]:
        """Take screenshot of page (optimized quality for storage)."""
        page = await self.navigate(url)
        if not page:
            return None
        
        try:
            if not path:
                path = f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
            
            # Medium quality to save space on SSD
            await page.screenshot(path=path, full_page=False, type="png")
            
            await page.close()
            self.stats["tasks_completed"] += 1
            
            return path
            
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            await page.close()
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            **self.stats,
            "mode": self.mode,
            "initialized": self.is_initialized,
            "active_tasks": self.active_tasks,
            "memory_current_mb": self._get_memory_usage() if self.is_initialized else 0,
            "ram_total_gb": round(self.total_ram_gb, 1),
            "cpu_cores": self.cpu_count
        }
    
    async def upgrade_mode(self, new_mode: str) -> bool:
        """Dynamically upgrade to more powerful mode."""
        if new_mode not in ["lightweight", "balanced", "full"]:
            return False
        
        if new_mode == "full" and self.total_ram_gb < 12:
            logger.warning("Cannot enable full mode with < 12GB RAM")
            return False
        
        self.mode = new_mode
        if new_mode == "lightweight":
            self.max_memory_mb = 300
            self.vision_enabled = False
        elif new_mode == "balanced":
            self.max_memory_mb = 600
            self.vision_enabled = True
        else:  # full
            self.max_memory_mb = 1000
            self.vision_enabled = True
        
        logger.info("🔄 Switched to %s mode", new_mode.upper())
        return True