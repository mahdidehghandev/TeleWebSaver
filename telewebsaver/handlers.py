import logging
import os
from typing import Dict
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from .searxng import searxng_search
from .snapshot import render_page_to_pdf


logger = logging.getLogger("telewebsaver.handlers")


router = Router()
RESULT_URLS: Dict[str, str] = {}


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    text = (
        "سلام! 👋\n\n"
        "من ربات *TeleWebSaver* هستم.\n\n"
        "با دستور زیر می‌تونی در وب جستجو کنی و نسخه‌ی PDF از صفحه را ذخیره کنی:\n"
        "`/search <متن جستجو>`\n\n"
        "مثال:\n"
        "`/search python telegram bot tutorial`"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject) -> None:
    query = (command.args or "").strip() if command else ""
    if not query:
        await message.answer(
            "لطفاً متن جستجو را بعد از دستور وارد کن.\n"
            "مثال:\n"
            "`/search python telegram bot tutorial`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    searching_message = await message.answer("در حال جستجو... ⏳")

    try:
        results = await searxng_search(query, num_results=5)
    except Exception:
        await searching_message.edit_text(
            "❌ خطا در ارتباط با SearxNG. بعداً دوباره تلاش کن."
        )
        return

    if not results:
        await searching_message.edit_text("هیچ نتیجه‌ای پیدا نشد.")
        return

    text = f"نتایج برای: *{query}*"

    buttons: list[list[InlineKeyboardButton]] = []
    for idx, item in enumerate(results):
        title = item["title"] or "No title"
        url = item["url"]

        parsed = urlparse(url)
        domain = parsed.netloc or ""
        if domain.startswith("www."):
            domain = domain[4:]

        cb_id = f"r{message.chat.id}_{message.message_id}_{idx}"
        RESULT_URLS[cb_id] = url

        base_text = title
        if domain:
            base_text = f"{title} – {domain}"

        button_text = base_text if len(base_text) <= 64 else base_text[:61] + "..."

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=cb_id,
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await searching_message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


@router.callback_query(F.data)
async def on_result_button(callback: CallbackQuery) -> None:
    cb_id = callback.data or ""
    url = RESULT_URLS.get(cb_id)

    if not url:
        await callback.answer("این دکمه دیگر معتبر نیست. دوباره جستجو کن.", show_alert=True)
        return

    await callback.answer("در حال ساخت PDF از صفحه... ⏳", show_alert=False)

    pdf_path: str | None = None
    filename: str | None = None
    try:
        pdf_path, filename = await render_page_to_pdf(url)
    except Exception:
        logger.exception("Error while rendering page to PDF: %s", url)
        await callback.message.answer(
            "❌ خطا در ساخت PDF از صفحه. ممکن است سایت دسترسی را محدود کرده باشد یا مرورگر headless مشکل داشته باشد."
        )
        return

    try:
        send_name = filename or "page.pdf"
        document = FSInputFile(path=pdf_path, filename=send_name)
        await callback.message.answer_document(document)
    finally:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                logger.warning("Failed to remove temp file: %s", pdf_path)

