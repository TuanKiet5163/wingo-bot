from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json, os
from datetime import datetime

# ===== CẤU HÌNH =====
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATTERN = [5000, 10000, 15000, 25000]
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
        if h["result"] == "lose": losses += 1
        else: break
    return PATTERN[losses % len(PATTERN)]

# ===== LỆNH: /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    history = data["history"]
    balance = data["balance"]
    bet = get_next_bet(history)
    win, lose, profit = calc_stats(history, balance)

    warn = ""
    if profit >= TARGET_PROFIT:
        warn = "\n🎯 ĐÃ ĐẠT LÃI MỤC TIÊU"
    elif profit <= MAX_LOSS:
        warn = "\n⚠️ CẢNH BÁO: LỖ VƯỢT MỨC"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])
    await update.message.reply_text(
        f"📅 {get_today()}\n"
        f"💰 Số dư: {balance:,}đ\n"
        f"🎯 Cược tiếp: {bet:,}đ\n"
        f"✅ Thắng: {win:,}đ | ❌ Thua: {lose:,}đ\n"
        f"📈 Lời/lỗ: {profit:+,}đ{warn}",
        reply_markup=reply_markup
    )

# ===== XỬ LÝ NÚT BẤM =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    history = data["history"]
    balance = data["balance"]
    today = get_today()

    if query.data == "win" or query.data == "lose":
        bet = get_next_bet(history)
        amount = round(bet * 0.96) if query.data == "win" else -bet
        balance += amount
        history.append({"date": today, "result": query.data, "amount": bet})
        data["balance"] = balance
        data["history"] = history
        save_data(data)

    elif query.data == "reset":
        save_data({"history": [], "balance": INITIAL_BALANCE})

    elif query.data == "view":
        entries = [f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']:,}đ" for i, h in enumerate(history)]
        msg = "\n".join(entries) if entries else "📭 Chưa có lịch sử hôm nay."
        await query.edit_message_text(f"📊 Lịch sử hôm nay:\n{msg}")
        return

    # Gửi lại giao diện
    bet = get_next_bet(history)
    win, lose, profit = calc_stats(history, balance)
    warn = ""
    if profit >= TARGET_PROFIT:
        warn = "\n🎯 ĐÃ ĐẠT LÃI MỤC TIÊU"
    elif profit <= MAX_LOSS:
        warn = "\n⚠️ CẢNH BÁO: LỖ VƯỢT MỨC"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])
    await query.edit_message_text(
        f"📅 {get_today()}\n"
        f"💰 Số dư: {balance:,}đ\n"
        f"🎯 Cược tiếp: {bet:,}đ\n"
        f"✅ Thắng: {win:,}đ | ❌ Thua: {lose:,}đ\n"
        f"📈 Lời/lỗ: {profit:+,}đ{warn}",
        reply_markup=reply_markup
    )

# ===== /status =====
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    history = data["history"]
    balance = data["balance"]
    bet = get_next_bet(history)
    win, lose, profit = calc_stats(history, balance)
    await update.message.reply_text(
        f"📅 {get_today()}\n"
        f"💰 Số dư: {balance:,}đ\n"
        f"🎯 Cược tiếp theo: {bet:,}đ\n"
        f"✅ Thắng: {win:,}đ | ❌ Thua: {lose:,}đ\n"
        f"📈 Lời/lỗ: {profit:+,}đ"
    )

# ===== /resetvon =====
async def resetvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["balance"] = INITIAL_BALANCE
    save_data(data)
    await update.message.reply_text("🔁 Đã reset vốn về 500.000đ.")

# ===== /setvon <số> =====
async def setvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_balance = int(context.args[0])
        data = load_data()
        data["balance"] = new_balance
        save_data(data)
        await update.message.reply_text(f"✅ Đã đặt lại vốn: {new_balance:,}đ")
    except:
        await update.message.reply_text("❌ Sai cú pháp. Dùng: /setvon 123000")

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
