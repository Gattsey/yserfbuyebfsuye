# bot.py — Telegram Mini App with MP4 Ads + Auto Reward + Group Bonus
import os
import random
import asyncio
import json
from flask import Flask, request, render_template_string
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
import nest_asyncio

nest_asyncio.apply()

# ------------------------
# 🔧 Configuration
# ------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

# Groups for bonus joining
GROUPS = [
    {"name": "Loot Everything Fast", "url": "https://t.me/looteverythingfast"},
    {"name": "Loot Everything Fast 2", "url": "https://t.me/looteverythingfast2"}
]

# Ads hosted externally (Cloudinary)
AD_LINKS = [
    {"video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762335977/ad1.mp4_pepcsc.mp4"},
    {"video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762336514/ad2.mp4_dnuqew.mp4"}
]

# File to track who got bonus messages
USER_FILE = "users.json"
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# 🌐 Flask App
# ------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running!"

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(
    html,
    video_src=ad["video_url"],
    domain=DOMAIN,
    ad_id=ad_id,
    user_id=request.args.get("user_id", ""),  # user ID passed from Telegram
)
    return "Invalid Ad ID", 404

@app.route("/watched", methods=["POST"])
def ad_watched():
    """Called when user finishes watching ad"""
    data = request.get_json()
    user_id = data.get("user_id")
    
    if not user_id:
        return {"error": "Missing user_id"}, 400

    import random
    earnings = round(random.uniform(3, 5), 2)  # random ₹3.00 - ₹5.00
    msg1 = f"✅ Aapne ₹{earnings} kamaye! Ad dekhne ka dhanyavaad 🎉"
    msg2 = "💬 Kripya dono groups join karein aur Bonus section me claim karein!"

    try:
        asyncio.run(tg_app.bot.send_message(chat_id=user_id, text=msg1))
        asyncio.run(tg_app.bot.send_message(chat_id=user_id, text=msg2))
        return {"success": True}, 200
    except Exception as e:
        logger.error(f"Error sending messages: {e}")
        return {"error": str(e)}, 500

# ------------------------
# 🤖 Telegram Bot Logic
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["▶️ Ad Dekho", "💵 Balance"],
        ["👥 Refer & Earn", "🎁 Bonus"],
        ["⚙️ Extra"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Welcome! Ads dekho aur har ad dekhkar paise kamao!",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    users = load_users()

    if text == "▶️ Ad Dekho":
        ad_idx = random.randrange(len(AD_LINKS))
        user_id = update.message.from_user.id
        ad_url = f"{DOMAIN}/ad/{ad_idx}?user_id={user_id}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Ad Dekho", web_app=WebAppInfo(url=ad_url))]]
        )
        await update.message.reply_text(
            "📊 Ek ad dekhne ki current rate: ₹3–₹5\n\n👇 Neeche diye button par click karke ad dekho!",
            reply_markup=kb
        )

        # Send group join message only if user hasn't joined yet
        if not users.get(user_id, {}).get("joined_groups"):
            group_text = "📢 Bonus Alert:\nKripya in dono groups ko join karein aur apna ₹50 bonus claim karein:\n\n"
            for g in GROUPS:
                group_text += f"👉 [{g['name']}]({g['url']})\n"
            group_text += "\n📍 Bonus section me claim karein!"
            await update.message.reply_text(group_text, parse_mode="Markdown")
            users[user_id] = {"joined_groups": False}
            save_users(users)

    elif text == "🎁 Bonus":
        user_data = users.get(user_id, {})
        if user_data.get("joined_groups"):
            await update.message.reply_text("🎉 Aapka ₹50 bonus already claim ho chuka hai!")
        else:
            await update.message.reply_text("📢 Bonus claim karne ke liye dono groups join karein!")

    elif text == "💵 Balance":
        await update.message.reply_text("💰 Aapka current balance: ₹0.00 (demo).")

    elif text == "👥 Refer & Earn":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={update.message.from_user.id}"
        await update.message.reply_text(f"👥 Share karein aur earn karein:\n{ref_link}")

    elif text == "⚙️ Extra":
        await update.message.reply_text("⚙️ Extra options coming soon!")

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

    if not tg_app._initialized:
        await tg_app.initialize()
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
# 🚀 Start App
# ------------------------
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()


