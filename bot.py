from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import os
from datetime import datetime

# Token
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"
DATA_FILE = "data.json"

# Gấp thếp theo chiến lược
GAP_THEP = {
    "light": [5000, 10000, 15000, 25000],
    "medium": [10000, 20000, 40000],
    "hard": [20000, 40000, 80000, 160000]
}

# Cảnh báo
MAX_PROFIT = 100000
MAX_LOSS = -150000

def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

def read_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_next_bet(history, strategy):
    losses = 0
    for entry in reversed(history):
        if entry["date"] != datetime.now().strftime("%Y-%m-%d"):
            break
        if entry["result"] == "lose":
            losses += 1
        else:
            break
    levels = GAP_THEP.get(strategy, GAP_THEP["medium"])
    if losses == 0:
        return levels[0]
    elif losses < len(levels):
        return levels[losses]
    else:
        return levels[0]

def calc_stats(history):
    today = datetime.now().strftime("%Y-%m-%d")
    entries = [h for h in history if h["date"] == today]
    win = sum(h["amount"] for h in entries if h["result"] == "win")
    lose = sum(h["amount"] for h in entries if h["result"] == "lose")
    return win, lose

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    init_data()
    data = read_data()
    if user_id not in data:
        data[user_id] = {
            "history": [],
            "strategy": None,
            "initial_balance": 500000,
            "current_balance": 500000
        }
        write_data(data)

    user = data[user_id]
    if not user["strategy"]:
        keyboard = [[InlineKeyboardButton("📈 Nhẹ", callback_data="set_light"),
                     InlineKeyboardButton("Vừa", callback_data="set_medium"),
                     InlineKeyboardButton("Mạnh", callback_data="set_hard")]]
        await update.message.reply_text("🛠 Vui lòng chọn chiến lược gấp thếp trước khi chơi:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    bet = get_next_bet(user["history"], user["strategy"])
    win, lose = calc_stats(user["history"])
    profit = user["current_balance"] - user["initial_balance"]
    strategy = user["strategy"]

    warn = ""
    if profit >= MAX_PROFIT:
        warn = "\n🎉 Đã đạt lợi nhuận mục tiêu!"
    elif profit <= MAX_LOSS:
        warn = "\n⚠️ Đã chạm ngưỡng lỗ cho phép!"

    keyboard = [
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 LỊCH SỬ", callback_data="view"),
         InlineKeyboardButton("🔄 RESET", callback_data="reset")],
        [InlineKeyboardButton("📈 Nhẹ", callback_data="set_light"),
         InlineKeyboardButton("Vừa", callback_data="set_medium"),
         InlineKeyboardButton("Mạnh", callback_data="set_hard")]
    ]
    await update.message.reply_text(
        f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
        f"💰 Số dư: {user['current_balance']}đ (Vốn: {user['initial_balance']}đ)\n"
        f"📈 Lời/Lỗ: {profit:+}đ\n"
        f"🎯 Cược tiếp theo: {bet}đ (Chiến lược: {strategy})\n"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ" + warn,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    init_data()
    data = read_data()
    if user_id not in data:
        data[user_id] = {
            "history": [],
            "strategy": None,
            "initial_balance": 500000,
            "current_balance": 500000
        }

    user = data[user_id]
    today = datetime.now().strftime("%Y-%m-%d")

    if query.data.startswith("set_"):
        user["strategy"] = query.data.split("_")[1]
        write_data(data)
        await query.edit_message_text("✅ Đã chọn chiến lược. Gửi /start để bắt đầu!")
        return

    if not user["strategy"]:
        keyboard = [[InlineKeyboardButton("📈 Nhẹ", callback_data="set_light"),
                     InlineKeyboardButton("Vừa", callback_data="set_medium"),
                     InlineKeyboardButton("Mạnh", callback_data="set_hard")]]
        await query.edit_message_text("🛠 Vui lòng chọn chiến lược gấp thếp trước khi chơi:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data in ["win", "lose"]:
        bet = get_next_bet(user["history"], user["strategy"])
        user["history"].append({"date": today, "result": query.data, "amount": bet})
        if query.data == "win":
            user["current_balance"] += bet
        else:
            user["current_balance"] -= bet
        write_data(data)

    elif query.data == "reset":
        user["history"] = []
        user["current_balance"] = user["initial_balance"]
        write_data(data)

    elif query.data == "view":
        entries = [h for h in user["history"] if h["date"] == today]
        msg = "\n".join([
            f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']}đ"
            for i, h in enumerate(entries)
        ]) if entries else "📭 Chưa có lịch sử hôm nay."
        await query.edit_message_text(f"📊 Lịch sử hôm nay:\n{msg}")
        return

    bet = get_next_bet(user["history"], user["strategy"])
    win, lose = calc_stats(user["history"])
    profit = user["current_balance"] - user["initial_balance"]
    strategy = user["strategy"]

    warn = ""
    if profit >= MAX_PROFIT:
        warn = "\n🎉 Đã đạt lợi nhuận mục tiêu!"
    elif profit <= MAX_LOSS:
        warn = "\n⚠️ Đã chạm ngưỡng lỗ cho phép!"

    keyboard = [
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 LỊCH SỬ", callback_data="view"),
         InlineKeyboardButton("🔄 RESET", callback_data="reset")],
        [InlineKeyboardButton("📈 Nhẹ", callback_data="set_light"),
         InlineKeyboardButton("Vừa", callback_data="set_medium"),
         InlineKeyboardButton("Mạnh", callback_data="set_hard")]
    ]
    await query.edit_message_text(
        f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
        f"💰 Số dư: {user['current_balance']}đ (Vốn: {user['initial_balance']}đ)\n"
        f"📈 Lời/Lỗ: {profit:+}đ\n"
        f"🎯 Cược tiếp theo: {bet}đ (Chiến lược: {strategy})\n"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ" + warn,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Chạy bot
if __name__ == "__main__":
    import asyncio
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.run(app.run_polling())
