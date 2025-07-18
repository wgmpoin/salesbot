import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# Load .env jika ada
load_dotenv()

# Aktifkan logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konstanta
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Contoh: https://namabot.fly.dev/webhook

# === Handler /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif dan merespons perintah /start.")

# === Handler /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — Mulai bot\n/help — Bantuan")

# === Fungsi utama ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Jalankan webhook
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL,
    )

# Entry point
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
