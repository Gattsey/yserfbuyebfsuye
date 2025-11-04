import os
import random
import asyncio
from flask import Flask, request, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

# Your local video ads
AD_LINKS = [
    {"video_url": f"{DOMAIN}/static/ad1.mp4", "group_url": "https://t.me/looteverythingfast"},
    {"video_url": f"{DOMAIN}/static/ad2.mp4", "group_url": "https://t.me/looteverythingfast2"},
]

app = Flask(__name__, static_folder="static")

@app.route("/")
def home():
    return "✅ Telegram Mini App Bot is running!"

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        return render_template("index.html", video_link=ad["video_url"], redirect_link=ad["group_url"])
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
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]]
        )
        await query.message.reply_text("📺 Please watch this ad:", reply_markup=kb)

    elif query.data == "balance":
        await query.message.reply_text("💰 Balance: ₹0.00 (demo)")

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(f"👥 Refer your friends:\n{ref}")

# Telegram webhook
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_click))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return "OK", 200

async def set_webhook():
    url = f"{DOMAIN}/{BOT_TOKEN}"
    await tg_app.bot.set_webhook(url)
    print(f"✅ Webhook set: {url}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
