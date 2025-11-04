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

# ======================================
# 🔐 Configuration
# ======================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")

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

# ======================================
# Flask App
# ======================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Mini App Bot is running!"

@app.route("/ad/<int:ad_id>")
def ad_page(ad_id):
    if 0 <= ad_id < len(AD_LINKS):
        ad = AD_LINKS[ad_id]
        html = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    margin: 0;
                    background: black;
                    color: white;
                    text-align: center;
                    font-family: sans-serif;
                }}
                iframe {{
                    width: 100%;
                    height: 70vh;
                    border: none;
                }}
                button {{
                    background: #2ecc71;
                    border: none;
                    color: white;
                    padding: 15px 25px;
                    border-radius: 10px;
                    font-size: 18px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <iframe src="{ad['video_url']}" allow="autoplay"></iframe>
            <h3>🎬 Watch the full ad to continue!</h3>
            <a href="{ad['group_url']}"><button>Continue ▶️</button></a>
        </body>
        </html>
        """
        return render_template_string(html)
    return "Invalid Ad ID", 404


# ======================================
# Telegram Bot Logic
# ======================================
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
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Watch Ad", web_app=WebAppInfo(url=ad_url))]]
        )
        await query.message.reply_text("📺 Please watch this ad completely:", reply_markup=kb)

    elif query.data == "balance":
        await query.message.reply_text("💰 Your current balance: ₹0.00 (demo).")

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(f"👥 Share your referral link:\n{ref_link}")


# ======================================
# Telegram Webhook Setup
# ======================================
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_click))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    try:
        if not tg_app._initialized:
            await tg_app.initialize()
        if not tg_app._running:
            await tg_app.start()
        update = Update.de_json(request.get_json(force=True), tg_app.bot)
        await tg_app.process_update(update)
    except Exception as e:
        print("❌ Error processing update:", e)
    return "OK", 200


# ======================================
# Run & Set Webhook
# ======================================
async def set_webhook():
    url = f"{DOMAIN}/{BOT_TOKEN}"
    try:
        await tg_app.bot.set_webhook(url)
        print(f"✅ Webhook set successfully: {url}")
    except Exception as e:
        print("⚠️ Failed to set webhook:", e)

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
