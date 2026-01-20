import asyncio
import logging
from typing import Any, Dict, List

import requests

from .config import get_searxng_base_url


logger = logging.getLogger("telewebsaver.searxng")


async def searxng_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Call SearxNG JSON API and return simplified results.

    Each result is a dict with keys: title, url, snippet.
    """

    base_url = get_searxng_base_url()
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
    }

    def _do_request() -> List[Dict[str, Any]]:
        resp = requests.get(f"{base_url}/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []
        for item in data.get("results", [])[:num_results]:
            title = item.get("title") or "No title"
            url = item.get("url") or ""
            snippet = (
                item.get("content")
                or item.get("snippet")
                or item.get("description")
                or ""
            )

            if not url:
                continue

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        return results

    try:
        return await asyncio.to_thread(_do_request)
    except Exception:
        logger.exception("Error while querying SearxNG")
        raise

