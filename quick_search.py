# quick_search.py
import aiohttp, bs4
from typing import Optional

class QuickSearch:
    async def google(self, query: str) -> Optional[str]:
        url = "https://www.google.com/search"
        params = {"q": query, "hl": "en"}
        headers = {"User-Agent": "Mozilla/5.0"}
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(url, params=params, headers=headers) as r:
                txt = await r.text()
        soup = bs4.BeautifulSoup(txt, "lxml")
        for sel in ("div.hgKElc", "div.VwiC3b", "span.hgKElc"):
            if (ans := soup.select_one(sel)):
                return ans.get_text(strip=True)
        return None