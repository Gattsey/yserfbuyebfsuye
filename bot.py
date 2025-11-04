# bot.py — Telegram Mini App + Flask (Render)
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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load secure environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

app = Flask(__name__)

# Ad content setup
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

@app.route("/")
def home():
    return "✅ Telegram Mini App Bot is running fine!"

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(html, video_link=ad["video_url"], redirect_link=ad["group_url"])
    return "Invalid Ad ID", 404

# Telegram logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👁️ Watch Ad", callback_data="show_ad")],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👥 Refer", callback_data="refer"),
        ],
    ]
    await update.message.reply_text("👋 Welcome! Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_ad":
        ad_idx = random.randrange(len(AD_LINKS))
        ad_url = f"{DOMAIN}/ad/{ad_idx}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]])
        await query.message.reply_text("📺 Please watch this ad:", reply_markup=kb)

    elif query.data == "balance":
        await query.message.reply_text("💰 Your current balance: ₹0.00 (demo).")

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(f"👥 Share your referral link:\n{ref_link}")

# Initialize bot
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_click))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)

    async def process_update():
        await tg_app.initialize()
        await tg_app.process_update(update)

    asyncio.run(process_update())
    return "OK", 200

# Set webhook on startup
def set_webhook():
    try:
        url = f"{DOMAIN}/{BOT_TOKEN}"
        asyncio.run(tg_app.bot.set_webhook(url))
        print(f"✅ Webhook set successfully: {url}")
    except Exception as e:
        print("⚠️ Failed to set webhook:", e)

set_webhook()
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
