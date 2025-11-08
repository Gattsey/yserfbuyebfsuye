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
BOT_TOKEN = os.getenv("BOT_TOKEN")  # must be set in environment
DOMAIN = os.getenv("DOMAIN", "https://yserfbuyebfsuye.onrender.com")  # update to your render domain

# Groups to check (use the @username or t.me/username)
GROUP1_HANDLE = "@looteverythingfast"
GROUP2_HANDLE = "@looteverythingfast2"

GROUPS = [
    {"name": "Loot Everything Fast", "url": f"https://t.me/{GROUP1_HANDLE.lstrip('@')}"},
    {"name": "Loot Everything Fast 2", "url": f"https://t.me/{GROUP2_HANDLE.lstrip('@')}"}
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
    logger.info("🎥 WATCHED EVENT: %s", data)
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
                chat_id=int(user_id),
                text=f"✅ Aapne ₹{reward} kamaye! Ad dekhne ka dhanyavaad 🎉"
            )
            await tg_app.bot.send_message(
                chat_id=int(user_id),
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
            f"👉 {GROUPS[0]['url']}\n"
            f"👉 {GROUPS[1]['url']}\n\n"
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
# 🎁 BONUS BUTTON HANDLER (robust + immediate feedback)
# -------------------------------------------------
async def handle_bonus_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Immediately acknowledge the callback so the client unblocks
    try:
        await query.answer(text="Checking group membership...", show_alert=False)
    except Exception as e:
        logger.warning(f"query.answer failed: {e}")

    user_id = str(query.from_user.id)
    users = load_users()
    now = datetime.utcnow()

    # ensure user record exists
    if user_id not in users:
        users[user_id] = {"balance": 0.0, "joined_groups": False}

    # store identifying info
    users[user_id]["first_name"] = query.from_user.first_name or ""
    users[user_id]["username"] = query.from_user.username or ""
    user = users[user_id]
    last_bonus = user.get("last_bonus")

    # Try to change the button right away to show it's claimed (use edit_message_reply_markup)
    try:
        claimed_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Claimed", callback_data="none")]])
        # prefer query.edit_message_reply_markup to be robust
        await query.edit_message_reply_markup(reply_markup=claimed_kb)
    except Exception as e:
        # Not fatal — log and continue. This prevents the handler from crashing.
        logger.warning(f"Could not edit reply markup for {user_id}: {e}")

    # Now check group membership with safe exceptions
    group1_status = False
    group2_status = False

    try:
        m1 = await context.bot.get_chat_member(chat_id="@looteverythingfast", user_id=int(user_id))
        group1_status = m1.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Could not check membership for group1 for {user_id}: {e}")

    try:
        m2 = await context.bot.get_chat_member(chat_id="@looteverythingfast2", user_id=int(user_id))
        group2_status = m2.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Could not check membership for group2 for {user_id}: {e}")

    # CASE 1: Joined none
    if not group1_status and not group2_status:
        try:
            await query.message.reply_text(
                "🚫 You have not joined any of the required groups.\n\n"
                "Join both groups and try again:\n\n"
                "👉 https://t.me/looteverythingfast\n"
                "👉 https://t.me/looteverythingfast2"
            )
        except Exception as e:
            logger.error(f"Failed to send 'joined none' msg to {user_id}: {e}")
        logger.info(f"BONUS_NONE: user_id={user_id}")
        return

    # CASE 2: Joined only one group -> give ₹25
    if group1_status != group2_status:
        user["joined_groups"] = False
        user["joined_at"] = now.isoformat()
        user["last_bonus"] = now.isoformat()
        user["balance"] = user.get("balance", 0) + 25
        save_users(users)
        try:
            await query.message.reply_text(
                "⚠️ You have joined only one group.\n"
                "Please join both groups to earn full rewards next time:\n\n"
                "👉 https://t.me/looteverythingfast\n"
                "👉 https://t.me/looteverythingfast2\n\n"
                "✅ ₹25 bonus added!"
            )
        except Exception as e:
            logger.error(f"Failed to send 'one group' msg to {user_id}: {e}")
        logger.info(f"BONUS_ONE_GROUP: user_id={user_id}")
        return

    # CASE 3: Joined both groups -> handle 24h cooldown and add ₹50
    if group1_status and group2_status:
        if last_bonus:
            try:
                last_bonus_dt = datetime.fromisoformat(last_bonus)
            except Exception:
                last_bonus_dt = now - timedelta(days=1)
            diff = now - last_bonus_dt
            if diff < timedelta(hours=24):
                remaining = timedelta(hours=24) - diff
                h = int(remaining.total_seconds() // 3600)
                m = int((remaining.total_seconds() % 3600) // 60)
                s = int(remaining.total_seconds() % 60)
                try:
                    await query.message.reply_text(f"⏳ Please wait {h}h {m}m {s}s for your next bonus.")
                except Exception as e:
                    logger.error(f"Failed to send cooldown msg to {user_id}: {e}")
                return

        # Give ₹50
        user["joined_groups"] = True
        user["joined_at"] = user.get("joined_at") or now.isoformat()
        user["last_bonus"] = now.isoformat()
        user["balance"] = user.get("balance", 0) + 50
        save_users(users)
        try:
            await query.message.reply_text(
                "🎉 Thanks for joining both groups!\n"
                "Stay active there for big loots 💥\n\n"
                "✅ ₹50 bonus added!\n"
                "⏳ Please wait 24 hours for your next bonus."
            )
        except Exception as e:
            logger.error(f"Failed to send 'both groups' msg to {user_id}: {e}")
        logger.info(f"BONUS_BOTH_GROUPS: user_id={user_id}")
        return

# ------------------------
# Admin helper commands
# ------------------------
ADMIN_ID = int(os.getenv("8288030589", "0"))  # Set your admin numeric ID in env or replace here

async def list_claimers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    args = context.args or []
    n = int(args[0]) if args and args[0].isdigit() else 10
    users = load_users()

    items = []
    for uid, info in users.items():
        if info.get("joined_groups") or info.get("joined_at"):
            joined = info.get("joined_at") or ""
            items.append((joined, uid, info))
    items.sort(reverse=True)
    items = items[:n]

    if not items:
        await update.message.reply_text("No claimers found.")
        return

    lines = []
    for joined, uid, info in items:
        uname = f"@{info.get('username')}" if info.get("username") else "-"
        fname = info.get("first_name", "-")
        bal = info.get("balance", 0)
        lines.append(f"{uid}  | {uname} | {fname} | joined: {joined or '-'} | bal: ₹{bal}")
    await update.message.reply_text("\n".join(lines))

async def find_claimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /find <substring>")
        return

    q = " ".join(context.args).lower()
    users = load_users()
    matches = []
    for uid, info in users.items():
        if q in (info.get("username") or "").lower() or q in (info.get("first_name") or "").lower():
            matches.append((uid, info))
    if not matches:
        await update.message.reply_text("No matches found.")
        return

    lines = []
    for uid, info in matches:
        uname = f"@{info.get('username')}" if info.get("username") else "-"
        fname = info.get("first_name", "-")
        bal = info.get("balance", 0)
        joined = info.get("joined_at", "-")
        lines.append(f"{uid} | {uname} | {fname} | joined: {joined} | bal: ₹{bal}")
    await update.message.reply_text("\n".join(lines))

async def punish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /punish <user_id_or_username>")
        return

    key = context.args[0].lstrip("@")
    users = load_users()

    # numeric id
    if key.isdigit():
        target_id = key
    else:
        found = []
        for uid, info in users.items():
            if info.get("username") and info["username"].lower() == key.lower():
                found.append(uid)
        if len(found) == 0:
            await update.message.reply_text("No user with that username found in DB.")
            return
        if len(found) > 1:
            await update.message.reply_text("Multiple users found with that username. Use numeric id to punish.")
            return
        target_id = found[0]

    if target_id not in users:
        await update.message.reply_text("User not found in DB.")
        return

    users[target_id]["balance"] = users[target_id].get("balance", 0) - 60
    save_users(users)
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text="⚠️ Don't be oversmart! You have not joined the groups.\n₹60 deducted (₹50 bonus + ₹10 penalty for cheating)."
        )
    except Exception as e:
        logger.error(f"Failed to message punished user: {e}")
    await update.message.reply_text(f"✅ Deducted ₹60 from {target_id}. Current balance: ₹{users[target_id].get('balance',0)}")

# ------------------------
# 🔔 Webhook Integration and App start
# ------------------------
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
tg_app.add_handler(CallbackQueryHandler(handle_bonus_claim, pattern="bonus_claim"))
tg_app.add_handler(CommandHandler("list_claimers", list_claimers))
tg_app.add_handler(CommandHandler("find", find_claimer))
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
    # Start flask app (this will block)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))

if __name__ == "__main__":
    main()



