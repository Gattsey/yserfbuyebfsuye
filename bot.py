import os
import random
import asyncio
from flask import Flask, request, render_template, jsonify
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================================================
#  Configuration
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")  # e.g. https://yourapp.onrender.com

AD_LINKS = [
    {
        "video_url": "https://drive.google.com/uc?export=preview&id=1H5C52ZlESDjOuvZJwKGBKFEmy-FrwCQT",
        "reward": 3.12
    },
    {
        "video_url": "https://drive.google.com/uc?export=preview&id=1iBmWU4dWF3Sni6Fc-vn-3QSeS12g2wdD",
        "reward": 2.45
    },
]

# =========================================================
#  Flask app
# =========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot Running on Render!"

@app.route("/ad/<int:ad_id>/<int:user_id>")
def show_ad(ad_id, user_id):
    """Show video page (inside Telegram Mini App)"""
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        return render_template("index.html", video_link=ad["video_url"], user_id=user_id, reward=ad["reward"])
    return "Invalid ad ID", 404


@app.route("/watched", methods=["POST"])
async def watched():
    """Called when user clicks Continue button"""
    data = request.get_json()
    user_id = data.get("user_id")
    reward = data.get("reward")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    msg = f"✅ You earned ₹{reward:.2f}! Ad complete — thank you for watching 🎉"
    await tg_app.bot.send_message(chat_id=user_id, text=msg)
    return jsonify({"ok": True})


# =========================================================
#  Telegram bot handlers
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👁 Watch Ad", callback_data="watch")],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👥 Refer", callback_data="refer"),
        ],
    ]
    await update.message.reply_text(
        "🎬 Welcome! Watch ads and earn rewards 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "watch":
        ad_idx = random.randrange(len(AD_LINKS))
        ad_url = f"{DOMAIN}/ad/{ad_idx}/{query.from_user.id}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]]
        )
        await query.message.reply_text("📺 Please watch this ad fully:", reply_markup=kb)

    elif query.data == "balance":
        await query.message.reply_text("💰 Your balance: ₹0.00 (demo).")

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(f"👥 Share and earn:\n{ref}")


# =========================================================
#  Webhook
# =========================================================
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_click))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.process_update(update))
    return "OK", 200


# =========================================================
#  Webhook setup
# =========================================================
def set_webhook():
    url = f"{DOMAIN}/{BOT_TOKEN}"
    asyncio.run(tg_app.bot.set_webhook(url))
    print("✅ Webhook set to", url)

set_webhook()
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
