# bot.py — Telegram Mini App + Flask (Render version)
import os
import random
import asyncio
from flask import Flask, request, render_template_string
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import logging


# =======================
# 🔐 Configuration
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")  # 👈 Replace with your Render URL

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set. Please add it in Render → Environment.")

AD_LINKS = [
    {
        "video_url": "https://drive.google.com/file/d/1H5C52ZlESDjOuvZJwKGBKFEmy-FrwCQT/preview",
        "group_url": "https://t.me/looteverythingfast",
    },
    {
        "video_url": "https://drive.google.com/file/d/1iBmWU4dWF3Sni6Fc-vn-3QSeS12g2wdD/preview",
        "group_url": "https://t.me/looteverythingfast2",
    },
]


# =======================
# 🧩 Logging (for Render logs)
# =======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =======================
# Flask Web App
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Mini App Bot is running on Render!"

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    """Serve ad inside Telegram Mini App (Google Drive preview embed)."""
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(
            html,
            video_link=ad["video_url"],
            redirect_link=ad["group_url"],
        )
    return "Invalid Ad ID", 404


# =======================
# Telegram Bot Logic
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👁️ Watch Ad", callback_data="show_ad")],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👥 Refer", callback_data="refer"),
        ],
    ]
    await update.message.reply_text(
        "👋 Welcome! Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_ad":
        ad_idx = random.randrange(len(AD_LINKS))
        ad_url = f"{DOMAIN}/ad/{ad_idx}"

        # ✅ Opens inside Telegram Mini App (not browser)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]]
        )
        await query.message.reply_text(
            "📺 Please watch the full ad below:", reply_markup=keyboard
        )

    elif query.data == "balance":
        await query.message.reply_text("💰 Your current balance: ₹0.00 (demo).")

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(f"👥 Share your referral link:\n{ref_link}")


# =======================
# Telegram Webhook Setup
# =======================
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_click))


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle Telegram updates via webhook"""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, tg_app.bot)

        async def process_update():
            if not tg_app._initialized:
                await tg_app.initialize()
            await tg_app.process_update(update)

        asyncio.get_event_loop().create_task(process_update())
        return "OK", 200

    except Exception as e:
        logger.error(f"⚠️ Webhook error: {e}")
        return "ERROR", 500


# =======================
# Set Telegram Webhook
# =======================
def set_webhook():
    """Set Telegram webhook once on startup"""
    url = f"{DOMAIN}/{BOT_TOKEN}"
    try:
        asyncio.run(tg_app.bot.set_webhook(url))
        logger.info(f"✅ Webhook set successfully: {url}")
    except Exception as e:
        logger.error(f"⚠️ Failed to set webhook: {e}")


# =======================
# Run Flask App
# =======================
set_webhook()
application = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
