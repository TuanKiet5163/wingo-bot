from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import os
from datetime import datetime

# Token bot Telegram
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"

# Tên file lưu dữ liệu
DATA_FILE = "data.json"

# Khởi tạo file dữ liệu nếu chưa tồn tại
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

# Đọc dữ liệu
def read_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Ghi dữ liệu
def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Tính toán thống kê trong ngày
def calc_stats(history):
    today = datetime.now().strftime("%Y-%m-%d")
    entries = [h for h in history if h["date"] == today]
    win = sum([h["amount"] for h in entries if h["result"] == "win"])
    lose = sum([h["amount"] for h in entries if h["result"] == "lose"])
    total = win - lose
    return win, lose, total

# Tính tiền cược tiếp theo
def next_bet(history):
    if not history:
        return 10000
    last = history[-1]
    if last["result"] == "lose":
        return last["amount"] * 2
    else:
        return 10000

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    init_data()
    data = read_data()
    if user_id not in data:
        data[user_id] = {"history": []}
        write_data(data)

    history = data[user_id]["history"]
    win, lose, total = calc_stats(history)
    bet = next_bet(history)

    keyboard = [
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("🔄 RESET", callback_data="reset"),
         InlineKeyboardButton("📊 XEM", callback_data="view")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"💰 Số dư hôm nay: {total}đ\n"
        f"🎯 Cược tiếp theo: {bet}đ\n"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ\n"
        f"\n➡️ Chọn kết quả ván vừa chơi:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

# /reset command
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    init_data()
    data = read_data()
    data[user_id] = {"history": []}
    write_data(data)
    await update.message.reply_text("✅ Đã reset phiên chơi. Gửi /start để bắt đầu lại.")

# Callback từ nút bấm
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    init_data()
    data = read_data()
    if user_id not in data:
        data[user_id] = {"history": []}

    history = data[user_id]["history"]

    if query.data in ["win", "lose"]:
        amount = next_bet(history)
        history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "result": query.data,
            "amount": amount
        })
        write_data(data)

    elif query.data == "reset":
        data[user_id]["history"] = []
        write_data(data)

    elif query.data == "view":
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [h for h in history if h["date"] == today]
        if entries:
            msg = "\n".join([
                f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']}đ"
                for i, h in enumerate(entries)
            ])
        else:
            msg = "📭 Chưa có lịch sử hôm nay."
        await query.edit_message_text(f"📊 Lịch sử hôm nay:\n{msg}")
        return

    win, lose, total = calc_stats(history)
    bet = next_bet(history)

    keyboard = [
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("🔄 RESET", callback_data="reset"),
         InlineKeyboardButton("📊 XEM", callback_data="view")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"💰 Số dư hôm nay: {total}đ\n"
        f"🎯 Cược tiếp theo: {bet}đ\n"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ\n"
        f"\n➡️ Chọn kết quả ván vừa chơi:"
    )
    await query.edit_message_text(text, reply_markup=reply_markup)

# Main
if __name__ == "__main__":
    import asyncio
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.run(app.run_polling())
