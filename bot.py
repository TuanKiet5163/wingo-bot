from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json, os
from datetime import datetime
import asyncio

# ===== CẤU HÌNH =====
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATTERN = [5000, 10000, 15000, 25000]
INITIAL_BALANCE = 500000
ALERT_PROFIT = 100000
ALERT_LOSS = -150000
ALERT_STREAK = 3

# ===== DỮ LIỆU =====
def get_today(): return datetime.now().strftime("%Y-%m-%d")
def get_now_time(): return datetime.now().strftime("%H:%M:%S")
def get_file(): return os.path.join(DATA_DIR, f"{get_today()}.json")

def load_data():
    if os.path.exists(get_file()):
        with open(get_file(), "r") as f: return json.load(f)
    return {"balance": INITIAL_BALANCE, "history": []}

def save_data(data):
    with open(get_file(), "w") as f: json.dump(data, f)

def get_next_bet(history):
    losses = 0
    for h in reversed(history):
        if h["date"] != get_today(): break
        if h["result"] == "lose": losses += 1
        else: break
    return PATTERN[losses % len(PATTERN)]

def calc_stats(data):
    history = data["history"]
    balance = data["balance"]
    wins = sum(h["amount"] for h in history if h["result"] == "win")
    losses = sum(h["amount"] for h in history if h["result"] == "lose")
    profit = balance - INITIAL_BALANCE
    return wins, losses, profit

def lose_streak(history):
    count = 0
    for h in reversed(history):
        if h["date"] != get_today(): break
        if h["result"] == "lose": count += 1
        else: break
    return count

# ===== GIAO DIỆN =====
async def show_status(send_func):
    data = load_data()
    bet = get_next_bet(data["history"])
    wins, losses, profit = calc_stats(data)
    time = get_now_time()
    warn = ""
    if profit >= ALERT_PROFIT: warn += "\n🔔 ĐẠT MỤC TIÊU LÃI"
    if profit <= ALERT_LOSS: warn += "\n⚠️ LỖ QUÁ MỨC"
    if lose_streak(data["history"]) >= ALERT_STREAK: warn += "\n❗ THUA LIÊN TIẾP"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Xem lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])

    await send_func(
        f"📅 {get_today()} | 🕒 {time}\n"
        f"💰 Số dư: {data['balance']:,}đ\n"
        f"🎯 Cược tiếp theo: {bet:,}đ\n"
        f"✅ Tổng thắng: {wins:,}đ | ❌ Tổng thua: {losses:,}đ\n"
        f"📈 Lời/Lỗ: {profit:+,}đ{warn}",
        reply_markup=reply_markup
    )

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

async def resetvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["balance"] = INITIAL_BALANCE
    save_data(data)
    await update.message.reply_text("🔁 Đã reset vốn về 500.000đ.")
    await show_status(update.message.reply_text)

async def setvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        data = load_data()
        data["balance"] = amount
        save_data(data)
        await update.message.reply_text(f"✅ Đã đặt vốn: {amount:,}đ")
        await show_status(update.message.reply_text)
    except:
        await update.message.reply_text("❌ Sai cú pháp. Dùng: /setvon 123000")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_document(InputFile(get_file()), filename=os.path.basename(get_file()))

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    wins, losses, profit = calc_stats(data)
    total = len(data["history"])
    msg = f"""📊 TỔNG KẾT {get_today()}:
Số phiên: {total}
✅ Tổng thắng: {wins:,}đ
❌ Tổng thua: {losses:,}đ
📈 Lời/Lỗ: {profit:+,}đ
"""
    await update.message.reply_text(msg)

# ===== XỬ LÝ NÚT BẤM =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    history = data["history"]
    balance = data["balance"]

    if query.data == "reset":
        data = {"balance": INITIAL_BALANCE, "history": []}
        save_data(data)
        await show_status(query.edit_message_text)
        return

    if query.data == "view":
        if not history:
            await query.edit_message_text("📭 Chưa có lịch sử hôm nay.")
            return
        lines = [f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']:,}đ" for i, h in enumerate(history)]
        await query.edit_message_text("📊 Lịch sử hôm nay:\n" + "\n".join(lines[-15:]))
        return

    if query.data in ["win", "lose"]:
        bet = get_next_bet(history)
        if bet > balance and query.data == "lose":
            await query.edit_message_text("❌ Không đủ vốn để cược. Hãy /setvon hoặc /resetvon.")
            return
        amount = round(bet * 0.96) if query.data == "win" else -bet
        balance += amount
        history.append({"date": get_today(), "result": query.data, "amount": bet})
        data["balance"] = balance
        data["history"] = history
        save_data(data)

    await show_status(query.edit_message_text)

# ===== CHẠY BOT =====
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetvon", resetvon))
    app.add_handler(CommandHandler("setvon", setvon))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.run(app.run_polling())
