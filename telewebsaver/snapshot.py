import asyncio
import logging
import os
import re
import tempfile
from typing import Tuple

from playwright.sync_api import sync_playwright


logger = logging.getLogger("telewebsaver.snapshot")


def _sanitize_title_to_filename(title: str) -> str:
    """
    Convert a page title to a safe filename, keeping it reasonably short.
    """
    if not title:
        return "page.pdf"

    title = title.strip()
    title = re.sub(r"\s+", " ", title)
    safe = re.sub(r"[^A-Za-z0-9 _-]", "", title)
    if not safe:
        safe = "page"
    # Replace spaces with underscores
    safe = safe.replace(" ", "_")
    # Limit length
    safe = safe[:80]
    return f"{safe}.pdf"


async def render_page_to_pdf(url: str) -> Tuple[str, str]:
    """
    Render the given URL to a PDF using Playwright (headless Chromium).
    Returns a tuple of (pdf_path, filename) where filename is derived
    from the page title.
    """

    def _render() -> Tuple[str, str]:
        temp_dir = tempfile.mkdtemp()
        fd, pdf_path = tempfile.mkstemp(dir=temp_dir, suffix=".pdf")
        os.close(fd)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 2560, "height": 1440},
                device_scale_factor=2,
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            try:
                page.evaluate(
                    """
                    () => {
                      const texts = ['accept', 'agree', 'got it', 'ok', 'understand', 'accept all'];
                      const candidates = Array.from(document.querySelectorAll('button, [role="button"], a, div'));
                      for (const el of candidates) {
                        const t = (el.innerText || el.textContent || '').toLowerCase().trim();
                        if (!t) continue;
                        if (texts.some(x => t.includes(x))) {
                          try { el.click(); } catch (e) {}
                        }
                      }
                    }
                    """
                )
                page.wait_for_timeout(1000)
                page.wait_for_load_state("networkidle")
            except Exception:
                logger.debug("Cookie banner auto-accept script failed for %s", url)

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            try:
                title = page.title()
            except Exception:
                title = ""

            filename = _sanitize_title_to_filename(title)
            final_path = os.path.join(temp_dir, filename)

            page.pdf(
                path=final_path,
                format="A4",
                print_background=True,
                margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
            )

            context.close()
            browser.close()

        return final_path, filename

    return await asyncio.to_thread(_render)

