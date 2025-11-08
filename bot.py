# bot.py — Telegram Mini App with MP4 Ads + Auto Reward + Bonus + Admin Control
import os
import random
import asyncio
import json
import logging
import nest_asyncio
from datetime import datetime, timedelta
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
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# 🔧 Configuration
# ------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

GROUPS = [
    {"name": "Loot Everything Fast", "url": "https://t.me/looteverythingfast"},
    {"name": "Loot Everything Fast 2", "url": "https://t.me/looteverythingfast2"}
]

AD_LINKS = [
    {"video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762335977/ad1.mp4_pepcsc.mp4"},
    {"video_url": "https://res.cloudinary.com/dxatgmpv7/video/upload/v1762336514/ad2.mp4_dnuqew.mp4"}
]

USER_FILE = "users.json"
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

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
            user_id=request.args.get("user_id", "")
        )
    return "Invalid Ad ID", 404


@app.route("/watched", methods=["POST"])
def watched():
    data = request.get_json()
    print("🎥 WATCHED EVENT:", data)
    user_id = str(data.get("user_id"))

    if not user_id:
        return {"status": "error", "message": "No user_id provided"}, 400

    users = load_users()
    reward = round(random.uniform(3, 5), 2)

    if user_id not in users:
        users[user_id] = {"balance": 0.0, "joined_groups": False}

    users[user_id]["balance"] += reward
    save_users(users)

    async def notify_user():
        try:
            await tg_app.bot.send_message(
                chat_id=user_id,
                text=f"✅ Aapne ₹{reward} kamaye! Ad dekhne ka dhanyavaad 🎉"
            )
            await tg_app.bot.send_message(
                chat_id=user_id,
                text="📢 Please join both groups to claim your bonus in the Bonus section!"
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    import threading
    threading.Thread(target=lambda: asyncio.run(notify_user())).start()

    return {"status": "ok", "reward": reward}, 200

# ------------------------
# 🤖 Telegram Bot Logic
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["▶️ Ad Dekhe", "💵 Balance"],
        ["👥 Refer & Earn", "🎁 Bonus"],
        ["⚙️ Extra"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Welcome! Ads dekhe aur har ad dekhkar paise kamao!",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    users = load_users()

    if user_id not in users:
        users[user_id] = {"balance": 0.0, "joined_groups": False}
        save_users(users)

    if text == "▶️ Ad Dekhe":
        ad_idx = random.randrange(len(AD_LINKS))
        ad_url = f"{DOMAIN}/ad/{ad_idx}?user_id={user_id}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Ad Dekhe", web_app=WebAppInfo(url=ad_url))]]
        )
        await update.message.reply_text(
            "📊 Ek ad dekhne ki current rate: ₹3–₹5\n"
            "⚠️ Video khatam hone se pehle band nahi kariyega, nahi toh reward nahi milega.\n"
            "🪙 Neeche diye gaye button ko dabaye aur ad dekhna shuru kare:",
            reply_markup=kb
        )

        if not users[user_id]["joined_groups"]:
            group_text = "📢 Bonus Alert:\nKripya in dono groups ko join karein aur apna ₹50 bonus claim karein:\n\n"
            for g in GROUPS:
                group_text += f"👉 [{g['name']}]({g['url']})\n"
            await update.message.reply_text(group_text, parse_mode="Markdown")

    elif text == "💵 Balance":
        bal = round(users[user_id].get("balance", 0.0), 2)
        await update.message.reply_text(f"💰 Available Balance: ₹{bal}")

    elif text == "🎁 Bonus":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Joined", callback_data="bonus_claim")]
        ])
        await update.message.reply_text(
            "🎁 Join both groups below and press '✅ I Joined' to claim your ₹50 bonus:\n\n"
            "👉 [Loot Everything Fast](https://t.me/looteverythingfast)\n"
            "👉 [Loot Everything Fast 2](https://t.me/looteverythingfast2)\n\n"
            "After joining, press the button below 👇",
            reply_markup=kb,
            parse_mode="Markdown"
        )

    elif text == "👥 Refer & Earn":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(f"👥 Apna referral link share karein:\n{ref_link}")

    elif text == "⚙️ Extra":
        await update.message.reply_text("⚙️ Extra options coming soon!")

# -------------------------------------------------
# 🎁 BONUS BUTTON HANDLER (✅ I Joined)
# -------------------------------------------------
async def handle_bonus_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    users = load_users()
    now = datetime.utcnow()

    if user_id not in users:
        users[user_id] = {"balance": 0.0, "joined_groups": False}

    user = users[user_id]
    joined_at = user.get("joined_at")
    last_bonus = user.get("last_bonus")

    # First-time claim
    if not user["joined_groups"]:
        user["joined_groups"] = True
        user["joined_at"] = now.isoformat()
        user["last_bonus"] = now.isoformat()
        user["balance"] += 50
        save_users(users)
        await query.message.reply_text("🎉 ₹50 bonus added! Come back every 24 hours for your next bonus.")
        return

    # Daily 24-hour bonus
    if last_bonus:
        last_bonus_dt = datetime.fromisoformat(last_bonus)
        if now - last_bonus_dt >= timedelta(hours=24):
            user["balance"] += 50
            user["last_bonus"] = now.isoformat()
            save_users(users)
            await query.message.reply_text("🎁 ₹50 daily bonus added! See you again tomorrow 🎉")
            return
        else:
            remaining = timedelta(hours=24) - (now - last_bonus_dt)
            hours_left = int(remaining.total_seconds() // 3600)
            await query.message.reply_text(f"⏳ Please wait {hours_left} more hours for your next bonus.")
            return

    await query.message.reply_text("✅ You already have your current bonus.")

# -------------------------------------------------
# ⚠️ ADMIN COMMAND: PUNISH CHEATERS
# -------------------------------------------------
ADMIN_ID = 8288030589  # 👈 Replace with your Telegram user ID

async def punish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /punish <user_id>")
        return

    target_id = context.args[0]
    users = load_users()

    if target_id in users:
        users[target_id]["balance"] -= 60
        save_users(users)
        await context.bot.send_message(
            chat_id=target_id,
            text="⚠️ Don't be oversmart! You have not joined the groups.\n₹60 deducted (₹50 bonus + ₹10 penalty for cheating)."
        )
        await update.message.reply_text(f"✅ Deducted ₹60 from user {target_id}.")
    else:
        await update.message.reply_text("User not found in database.")

# ------------------------
# 🔔 Webhook Integration
# ------------------------
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
tg_app.add_handler(CallbackQueryHandler(handle_bonus_claim, pattern="bonus_claim"))
tg_app.add_handler(CommandHandler("punish", punish))

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

