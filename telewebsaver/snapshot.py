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
            try:
                page.goto(url, wait_until="load", timeout=30000)
            except Exception:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    logger.warning("Page load timeout for %s: %s", url, e)
                    raise

            try:
                page.wait_for_timeout(1000)
                
                page.add_style_tag(content="""
                    [class*="cookie"],
                    [id*="cookie"],
                    [class*="consent"],
                    [id*="consent"],
                    [class*="gdpr"],
                    [id*="gdpr"],
                    [class*="privacy-banner"],
                    [id*="privacy-banner"],
                    [class*="cookie-banner"],
                    [id*="cookie-banner"],
                    [class*="cookie-consent"],
                    [id*="cookie-consent"],
                    [class*="cookie-notice"],
                    [id*="cookie-notice"] {
                        display: none !important;
                        visibility: hidden !important;
                        opacity: 0 !important;
                        height: 0 !important;
                        overflow: hidden !important;
                        position: absolute !important;
                        z-index: -9999 !important;
                    }
                """)
                
                page.evaluate("""
                    () => {
                        document.cookie = "cookie_consent=true; path=/; max-age=31536000";
                        document.cookie = "cookieconsent_status=allow; path=/; max-age=31536000";
                        document.cookie = "consent=yes; path=/; max-age=31536000";
                        document.cookie = "gdpr_consent=true; path=/; max-age=31536000";
                        document.cookie = "cookie_agreed=true; path=/; max-age=31536000";
                        document.cookie = "cookies_accepted=true; path=/; max-age=31536000";
                        
                        try {
                            localStorage.setItem('cookie_consent', 'true');
                            localStorage.setItem('cookieconsent_status', 'allow');
                            localStorage.setItem('consent', 'yes');
                            localStorage.setItem('gdpr_consent', 'true');
                            localStorage.setItem('cookie_agreed', 'true');
                            localStorage.setItem('cookies_accepted', 'true');
                        } catch(e) {}
                        
                        try {
                            sessionStorage.setItem('cookie_consent', 'true');
                            sessionStorage.setItem('cookieconsent_status', 'allow');
                        } catch(e) {}
                        
                        const banners = document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"], [class*="gdpr"], [id*="gdpr"]');
                        banners.forEach(banner => {
                            if (banner) {
                                banner.style.display = 'none';
                                banner.style.visibility = 'hidden';
                                banner.remove();
                            }
                        });
                    }
                """)
                
                page.wait_for_timeout(1000)
            except Exception:
                logger.debug("Cookie banner bypass failed for %s", url)

            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            
            try:
                page.evaluate("() => document.fonts.ready")
            except Exception:
                pass
            
            page.wait_for_timeout(3000)
            
            try:
                page.wait_for_selector("body", state="visible", timeout=5000)
            except Exception:
                pass

            try:
                title = page.title()
            except Exception:
                title = ""

            scroll_height = page.evaluate("() => document.documentElement.scrollHeight")
            scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
            
            MAX_WIDTH = 8000
            MAX_HEIGHT = 50000
            
            width_px = min(max(scroll_width, 2560), MAX_WIDTH)
            height_px = min(max(scroll_height, 1440), MAX_HEIGHT)

            filename = _sanitize_title_to_filename(title)
            final_path = os.path.join(temp_dir, filename)

            try:
                page.pdf(
                    path=final_path,
                    width=f"{width_px}px",
                    height=f"{height_px}px",
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
            except Exception as e:
                logger.warning("Failed to generate PDF with custom dimensions, falling back to A4: %s", e)
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

