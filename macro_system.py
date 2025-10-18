# macro_system.py
import asyncio
from typing import List

class MacroSystem:
    macros = {
        "work mode": ["open vscode", "open chrome", "search in chrome github", "in spotify play lofi hip hop"],
        "gaming mode": ["open steam", "open discord", "in discord mute", "close chrome"],
        "shutdown": ["close all apps", "save notepad", "goodbye"],
    }

    def __init__(self, proc): self.proc = proc

    async def run(self, name: str) -> None:
        if name not in self.macros: return
        await self.proc.speak(f"Running {name} macro")
        for cmd in self.macros[name]:
            await self.proc.execute(cmd)
            await asyncio.sleep(0.3)