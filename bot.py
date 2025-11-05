# bot.py — Telegram Mini App with Local MP4 Ads + Reply Keyboard
import json
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

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Local video ads (must be in /static directory)
AD_LINKS = [
    {
        "video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762335977/ad1.mp4_pepcsc.mp4",
        "group_url": "https://t.me/looteverythingfast"
    },
    {
        "video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762336514/ad2.mp4_dnuqew.mp4",
        "group_url": "https://t.me/looteverythingfast2"
    },
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
    user_id = request.args.get("user_id", "unknown")
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(
            html,
            video_src=ad["video_url"],
            redirect_link=ad["group_url"],
        )
    return "Invalid Ad ID", 404

@app.route("/watched/<int:user_id>/<int:ad_id>")
def ad_watched(user_id, ad_id):
    """Called automatically when ad is fully watched"""
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {"balance": 0, "joined_groups": False}

    reward = round(random.uniform(3, 5), 2)
    users[str(user_id)]["balance"] += reward
    save_users(users)

    asyncio.create_task(send_reward_messages(user_id, reward))
    return "ok"

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
        "👀 Ads dekho, har ek ad dekhne pe paise kamayo!",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id  # get user ID

    if text == "▶️ Ad Dekho":
        ad_idx = random.randrange(len(AD_LINKS))
        # include user_id in URL so /watched route can track who watched
        ad_url = f"{DOMAIN}/ad/{ad_idx}?user_id={user_id}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Ad Dekho", web_app=WebAppInfo(url=ad_url))]]
        )
        await update.message.reply_text(
            """📊 Ek ad dekhne ki current rate: ₹ 3–5

⚠️ Video khatam hone se pehle band mat karna, nahi toh reward nahi milega.

👇 Neeche diye button ko dabao aur ad dekhna shuru karo!""",
            reply_markup=kb
        )

    elif text == "💵 Balance":
        users = load_users()
        balance = users.get(str(user_id), {}).get("balance", 0)
        await update.message.reply_text(f"💰 Aapka current balance: ₹{balance:.2f}")

    elif text == "👥 Refer & Earn":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={update.message.from_user.id}"
        await update.message.reply_text(f"👥 Apna referral link share kare:\n{ref_link}")

    elif text == "🎁 Bonus":
        await update.message.reply_text("🎁 Jaldi hi bonus feature launch hoga!")

    elif text == "⚙️ Extra":
        await update.message.reply_text("⚙️ Settings aur extra options coming soon!")

async def send_reward_messages(user_id, reward):
    """Send earning message and group join reminder"""
    try:
        await tg_app.bot.send_message(
            chat_id=user_id,
            text=f"✅ Aapne ₹{reward} kamaye! Ad dekhne ka dhanyavaad! 🎉"
        )

        users = load_users()
        if not users[str(user_id)]["joined_groups"]:
            await tg_app.bot.send_message(
                chat_id=user_id,
                text=(
                    "📢 Bonus Reminder:\n\n"
                    "Please join both groups and claim your bonus in the *Bonus* section!\n\n"
                    "👉 [Group 1](https://t.me/looteverythingfast)\n"
                    "👉 [Group 2](https://t.me/looteverythingfast2)"
                ),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.warning(f"Message send failed for {user_id}: {e}")

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

    # ✅ Ensure app initialized before processing
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
# 🚀 App Start
# ------------------------
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()

