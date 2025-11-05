# bot.py — Telegram Mini App with Local MP4 Ads + Reply Keyboard
import os
import random
import asyncio
from flask import Flask, request, render_template_string, send_from_directory
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import logging

# ------------------------
# 🔧 Configuration
# ------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local video ads (must be in /static directory)
AD_LINKS = [
    {"video_url": f"{DOMAIN}/static/ad1.mp4", "group_url": "https://t.me/looteverythingfast"},
    {"video_url": f"{DOMAIN}/static/ad2.mp4", "group_url": "https://t.me/looteverythingfast2"},
]

# ------------------------
# 🌐 Flask App
# ------------------------
app = Flask(__name__, static_folder="static")

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running!"

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    """Render video ad page for Mini App"""
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(
            html,
            video_src=f"{DOMAIN}/static/{ad['file']}",
            redirect_link=ad["group_url"],
        )
    return "Invalid Ad ID", 404

# ------------------------
# 🤖 Telegram Bot Logic
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["👁 Ad Dekho", "💰 Balance"],
        ["👥 Refer & Earn", "🎁 Bonus"],
        ["⚙️ Extra"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Welcome! Choose an option below:",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👁 Ad Dekho":
        ad_idx = random.randrange(len(AD_LINKS))
        ad_url = f"{DOMAIN}/ad/{ad_idx}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]]
        )
        await update.message.reply_text("📺 Please watch this ad completely:", reply_markup=kb)

    elif text == "💰 Balance":
        await update.message.reply_text("💰 Your current balance: ₹0.00 (demo).")

    elif text == "👥 Refer & Earn":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={update.message.from_user.id}"
        await update.message.reply_text(f"👥 Share your referral link:\n{ref_link}")

    elif text == "🎁 Bonus":
        await update.message.reply_text("🎁 Your daily bonus feature will be added soon!")

    elif text == "⚙️ Extra":
        await update.message.reply_text("⚙️ Settings and more options coming soon!")

# ------------------------
# 🔔 Webhook Integration
# ------------------------
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return "OK", 200

async def set_webhook():
    url = f"{DOMAIN}/{BOT_TOKEN}"
    try:
        await tg_app.bot.set_webhook(url)
        logger.info(f"✅ Webhook set to {url}")
    except Exception as e:
        logger.error(f"⚠️ Webhook setup failed: {e}")

# ------------------------
# 🚀 App Start
# ------------------------
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()

