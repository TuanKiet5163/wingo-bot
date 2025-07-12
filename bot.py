from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json, os
from datetime import datetime

# ===== CẤU HÌNH =====
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATTERN = [5000, 10000, 15000, 25000]  # chu kỳ cược tuần hoàn
TARGET_PROFIT = 100000
MAX_LOSS = -150000
INITIAL_BALANCE = 500_000

# ===== LƯU / TẢI DỮ LIỆU =====
def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_data_file():
    return os.path.join(DATA_DIR, f"{get_today()}.json")

def load_data():
    file = get_data_file()
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {"history": [], "balance": INITIAL_BALANCE}

def save_data(data):
    with open(get_data_file(), "w") as f:
        json.dump(data, f)

# ===== TÍNH TOÁN =====
def calc_stats(history, balance):
    win = sum(h["amount"] for h in history if h["result"] == "win")
    lose = sum(h["amount"] for h in history if h["result"] == "lose")
    profit = balance - INITIAL_BALANCE
    return win, lose, profit

def get_next_bet(history):
    losses = 0
    for h in reversed(history):
        if h["date"] != get_today(): break
        if h["result"] == "lose":
            losses += 1
        else:
            break
    return PATTERN[losses % len(PATTERN)]

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

# ===== HIỂN THỊ TRẠNG THÁI =====
async def show_status(send_func):
    data = load_data()
    history = data["history"]
    balance = data["balance"]
    bet = get_next_bet(history)
    win, lose, profit = calc_stats(history, balance)

    warn = ""
    if profit >= TARGET_PROFIT:
        warn = "\n🎯 ĐẠT MỤC TIÊU LÃI"
    elif profit <= MAX_LOSS:
        warn = "\n⚠️ VƯỢT NGƯỠNG LỖ!"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])
    await send_func(
        f"📅 {get_today()}\n"
        f"💰 Số dư: {balance:,}đ\n"
        f"🎯 Cược tiếp: {bet:,}đ\n"
        f"✅ Thắng: {win:,}đ | ❌ Thua: {lose:,}đ\n"
        f"📈 Lãi/Lỗ: {profit:+,}đ{warn}",
        reply_markup=reply_markup
    )

# ===== /status =====
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

# ===== /resetvon =====
async def resetvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["balance"] = INITIAL_BALANCE
    save_data(data)
    await update.message.reply_text("🔁 Đã reset vốn về 500.000đ.")
    await show_status(update.message.reply_text)

# ===== /setvon <số> =====
async def setvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_balance = int(context.args[0])
        if new_balance < 10000:
            raise ValueError
        data = load_data()
        data["balance"] = new_balance
        save_data(data)
        await update.message.reply_text(f"✅ Đã đặt lại vốn: {new_balance:,}đ")
        await show_status(update.message.reply_text)
    except:
        await update.message.reply_text("❌ Sai cú pháp. Dùng: /setvon 123000")

# ===== NÚT WIN/LOSE/RESET/VIEW =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()
    history = data["history"]
    balance = data["balance"]
    bet = get_next_bet(history)

    if query.data in ["win", "lose"]:
        if bet > balance and query.data == "lose":
            await query.edit_message_text("❌ Không đủ số dư để cược! Hãy /resetvon hoặc /setvon.")
            return

        amount = round(bet * 0.96) if query.data == "win" else -bet
        balance += amount
        history.append({"date": get_today(), "result": query.data, "amount": bet})
        data["balance"] = balance
        data["history"] = history
        save_data(data)

    elif query.data == "reset":
        data = {"history": [], "balance": INITIAL_BALANCE}
        save_data(data)

    elif query.data == "view":
        if not history:
            await query.edit_message_text("📭 Chưa có lịch sử hôm nay.")
            return
        lines = [f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']:,}đ" for i, h in enumerate(history)]
        msg = "\n".join(lines)
        await query.edit_message_text(f"📊 Lịch sử hôm nay:\n{msg}")
        return

    await show_status(query.edit_message_text)

# ===== CHẠY BOT =====
if __name__ == "__main__":
    import asyncio
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetvon", resetvon))
    app.add_handler(CommandHandler("setvon", setvon))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.run(app.run_polling())
