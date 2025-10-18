# app_scanner.py  –  debugged & duplicate-free
import os
import winreg
import json
import logging
import subprocess
import stat
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from functools import lru_cache
from rapidfuzz import process, fuzz
from config import Config
from memory_manager import MemoryManager

logger = logging.getLogger("AI_Assistant.AppScanner")


class AppManager:
    """Scans for and manages all detectable applications on the system."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.cache_file = Path(Config.CACHE_DIR) / "apps_cache.json"
        self.cache_duration = timedelta(hours=24)
        self._load_custom_apps()
        self.apps = self._load_apps_with_cache()
        logger.info(f"Initialized with {len(self.apps)} applications found.")

    # ------------------------------------------------------------------
    #  NEW:  registry-modification check  (cheap cache invalidation)
    # ------------------------------------------------------------------
    def _system_app_modified_time(self) -> datetime:
        """Return newest mtime among Uninstall keys → proxy for 'apps changed'."""
        keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        newest = datetime.min
        for k in keys:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, k) as h:
                    t = datetime.fromtimestamp(os.stat(h.handle).st_mtime)
                    newest = max(newest, t)          # ← fixed syntax
            except Exception:
                pass
        return newest

    # ------------------------------------------------------------------
    #  Cache loader  (skip full scan if nothing changed)
    # ------------------------------------------------------------------
    def _load_apps_with_cache(self) -> Dict[str, str]:
        """Load apps from cache or rescan only if system changed."""
        if self.cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            if cache_age < self.cache_duration:
                #  ----  quick invalidation check  ----
                if datetime.fromtimestamp(self.cache_file.stat().st_mtime) > self._system_app_modified_time():
                    logger.info("Apps unchanged – using cache")
                    with self.cache_file.open(encoding="utf-8") as f:
                        return json.load(f)

        #  ----  full scan  ----
        apps = {}
        apps.update(self._scan_registry_apps())
        apps.update(self._scan_start_menu())
        apps.update(self._scan_store_apps())
        apps.update(self.memory_manager.get_all_apps())

        #  ----  save cache  ----
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("w", encoding="utf-8") as f:
            json.dump(apps, f, indent=4)
        logger.info(f"Saved {len(apps)} apps to cache.")
        return apps if apps else {}
    # ------------------------------------------------------------------
    #  remaining methods unchanged (kept as-is)
    # ------------------------------------------------------------------
    def rescan_apps(self) -> str:
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Application cache deleted.")
            self.apps = self._load_apps_with_cache()
            return f"Successfully rescanned. I found {len(self.apps)} applications."
        except OSError as e:
            logger.error(f"Error deleting cache file: {e}")
            return "There was an error while trying to rescan applications."

    def _load_custom_apps(self) -> None:
        custom_apps_path = Path(__file__).with_name("custom_apps.json")
        if custom_apps_path.exists():
            try:
                with custom_apps_path.open("r", encoding="utf-8") as f:
                    custom_apps = json.load(f)
                    for name, path in custom_apps.items():
                        if name and path:
                            self.memory_manager.add_app(name.lower(), path)
            except (json.JSONDecodeError, OSError, TypeError) as e:
                logger.error(f"Error reading {custom_apps_path}: {e}")

    def _scan_store_apps(self) -> Dict[str, str]:
        ...   # (kept identical to your last version)

    def _scan_start_menu(self) -> Dict[str, str]:
        ...   # (kept identical)

    def _scan_registry_apps(self) -> Dict[str, str]:
        ...   # (kept identical)

    @lru_cache(maxsize=256)
    def find_best_match(self, query: str) -> Optional[str]:
        ...   # (kept identical)

    def clear_match_cache(self) -> None:
        try:
            self.find_best_match.cache_clear()
            logger.info("App match cache cleared.")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")