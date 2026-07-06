import os
import logging
import random
import string
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from db import save_movie, get_movie_by_key, key_exists
from tmdb import search_poster
from ai import generate_description

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
SOURCE_CHANNEL_ID = int(os.environ["SOURCE_CHANNEL_ID"])
DEST_CHANNEL_ID = int(os.environ["DEST_CHANNEL_ID"])
KEY_LENGTH = int(os.environ.get("KEY_LENGTH", "6"))


def generate_key(length: int = KEY_LENGTH) -> str:
    """Generate a short random key (letters + digits) that isn't already used."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        candidate = "".join(random.choices(alphabet, k=length))
        if not key_exists(candidate):
            return candidate
    raise RuntimeError("Could not generate a unique key after 20 attempts")


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fires when a new video/document is posted in the SOURCE channel."""
    post = update.channel_post
    if post is None or post.chat_id != SOURCE_CHANNEL_ID:
        return
    if not (post.video or post.document):
        return

    caption = (post.caption or "").strip()
    if not caption:
        await context.bot.send_message(
            chat_id=SOURCE_CHANNEL_ID,
            text="⚠️ این فیلم بدون کپشن فرستاده شد. لطفاً دوباره بفرست؛ خط اول کپشن باید اسم فیلم باشه.",
        )
        return

    lines = [l.strip() for l in caption.splitlines() if l.strip()]
    movie_title = lines[0]
    extra_info = " ".join(lines[1:]) if len(lines) > 1 else ""

    overview = generate_description(movie_title, extra_info)
    poster_url = search_poster(movie_title)

    key = generate_key()

    save_movie(
        key=key,
        source_chat_id=post.chat_id,
        source_message_id=post.message_id,
        title=movie_title,
        overview=overview,
        poster_url=poster_url,
    )

    caption = (
        f"🎬 *{movie_title}*\n\n"
        f"{overview}\n\n"
        f"🔑 کلید دریافت: `{key}`\n\n"
        f"برای دریافت فیلم، همین کلید رو برای ربات بفرست."
    )

    if poster_url:
        await context.bot.send_photo(
            chat_id=DEST_CHANNEL_ID,
            photo=poster_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await context.bot.send_message(
            chat_id=DEST_CHANNEL_ID,
            text=caption,
            parse_mode=ParseMode.MARKDOWN,
        )

    logger.info("Registered movie '%s' with key %s", movie_title, key)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! کلیدی که از کانال گرفتی رو برام بفرست تا فیلم رو برات بفرستم."
    )


async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    text = (update.message.text or "").strip().upper()
    if not text:
        return

    movie = get_movie_by_key(text)
    if not movie:
        await update.message.reply_text("❌ کلید نامعتبره. لطفاً دوباره چک کن و بفرست.")
        return

    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=int(movie["source_chat_id"]),
            message_id=movie["source_message_id"],
        )
    except Exception:
        logger.exception("Failed to copy message")
        await update.message.reply_text(
            "⚠️ مشکلی در ارسال فیلم پیش اومد. مطمئن شو ربات هنوز توی کانال منبع ادمینه."
        )


def start_health_server():
    """A tiny HTTP server so Render's free 'web service' tier keeps the process alive."""
    port = int(os.environ.get("PORT", 8080))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def log_message(self, format, *args):
            pass

    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


def main():
    threading.Thread(target=start_health_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_private_message)
    )

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
