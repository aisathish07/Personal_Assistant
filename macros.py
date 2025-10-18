from typing import List
import asyncio
class MacroSystem:
    macros = {
        "work mode": ["open vscode", "open chrome", "search in chrome github", "in spotify play lofi hip hop"],
        "gaming mode": ["open steam", "open discord", "in discord mute", "close chrome"],
        "shutdown": ["close all apps", "save notepad", "goodbye"],
    }
    def __init__(self, proc): self.proc = proc
    async def run(self, name: str):
        for cmd in self.macros.get(name, []):
            await self.proc.execute(cmd)
            await asyncio.sleep(0.3)