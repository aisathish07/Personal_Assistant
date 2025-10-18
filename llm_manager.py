# llm_manager.py – unified Gemini + Ollama router with thread safety
from __future__ import annotations

import asyncio
import aiohttp
import logging
import random
from typing import Optional, Callable, Any
from threading import Lock

from config import Config
from async_utils import async_retry

logger = logging.getLogger("AI_Assistant.LLM")

_ollama_session: Optional[aiohttp.ClientSession] = None
_gemini_session: Optional[aiohttp.ClientSession] = None
_ollama_init = False
_gemini_init = False
_session_lock = Lock()


# ----------  session lifecycle  ----------
async def close_sessions() -> None:
    global _ollama_session, _gemini_session
    with _session_lock:
        if _ollama_session:
            await _ollama_session.close()
            _ollama_session = None
        if _gemini_session:
            await _gemini_session.close()
            _gemini_session = None
    logger.info("LLM sessions closed.")


async def _get_or_create_gemini_session() -> aiohttp.ClientSession:
    """Thread-safe gemini session getter/creator."""
    global _gemini_session, _gemini_init
    with _session_lock:
        if not _gemini_init:
            _gemini_session = aiohttp.ClientSession()
            _gemini_init = True
    return _gemini_session


async def _get_or_create_ollama_session() -> aiohttp.ClientSession:
    """Thread-safe ollama session getter/creator."""
    global _ollama_session, _ollama_init
    with _session_lock:
        if not _ollama_init:
            _ollama_session = aiohttp.ClientSession()
            _ollama_init = True
    return _ollama_session


# ----------  Gemini  ----------
@async_retry()
async def get_gemini_response(prompt: str) -> Optional[str]:
    if not Config.GEMINI_API_KEY:
        return None
    
    session = await _get_or_create_gemini_session()
    headers = {"Content-Type": "application/json"}
    models = Config.GEMINI_MODELS[:]
    if Config.RANDOMIZE_MODELS:
        random.shuffle(models)

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={Config.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "topP": 0.95}
        }
        try:
            logger.info("Trying Gemini model: %s", model)
            timeout = aiohttp.ClientTimeout(total=Config.GEMINI_TIMEOUT)
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                logger.info("Gemini model %s succeeded.", model)
                return reply
        except Exception as e:
            logger.warning("Gemini model %s failed: %s", model, e)
            continue
    return None


# ----------  Ollama  ----------
@async_retry(retries=2)
async def get_ollama_response(prompt: str) -> Optional[str]:
    session = await _get_or_create_ollama_session()
    models = Config.OLLAMA_MODELS[:]
    if Config.RANDOMIZE_MODELS:
        random.shuffle(models)

    for model in models:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        try:
            logger.info("Trying Ollama model: %s", model)
            timeout = aiohttp.ClientTimeout(total=Config.OLLAMA_TIMEOUT)
            async with session.post(
                f"{Config.OLLAMA_API_URL}/api/generate", json=payload, timeout=timeout
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if "error" in data:
                    logger.warning("Ollama model %s returned error: %s", model, data["error"])
                    continue
                reply = data.get("response", "").strip()
                logger.info("Ollama model %s succeeded.", model)
                return reply
        except Exception as e:
            logger.warning("Ollama model %s failed: %s", model, e)
            continue
    return None


# ----------  unified router  ----------
PROVIDERS = {
    "gemini": get_gemini_response,
    "ollama": get_ollama_response,
}


async def get_llm_response(
    prompt: str,
    provider: str = "gemini",
    status_callback: Optional[Callable[[str], None]] = None
) -> str:
    """Return reply string + trigger start/end status events."""
    # 1. choose order (local-first when LOCAL_ONLY)
    if Config.LOCAL_ONLY:
        providers = ["ollama", "gemini"]
    else:
        providers = ["gemini", "ollama"]

    # 2. skip missing keys
    if provider == "gemini" and not Config.GEMINI_API_KEY:
        if "gemini" in providers:
            providers.remove("gemini")
    if provider == "ollama" and not Config.OLLAMA_API_URL:
        if "ollama" in providers:
            providers.remove("ollama")

    if not providers:
        return "No LLM provider available (check keys / local service)."

    # 3. try each provider
    for prov in providers:
        if status_callback:
            status_callback(f"llm_{prov}_start")
        try:
            func = PROVIDERS[prov]
            reply = await func(prompt)
            if status_callback:
                status_callback(f"llm_{prov}_end")
            if reply:
                return reply
        except Exception as e:
            logger.error("Provider %s failed: %s", prov, e)
            if status_callback:
                status_callback(f"llm_{prov}_error")
            continue

    # 4. all failed
    return "All LLM providers failed."