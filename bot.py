from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json, os
from datetime import datetime

TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

GAP_THEP = [5000, 10000, 15000, 25000]
TARGET_PROFIT = 100000
MAX_LOSS = -150000

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_data_file():
    return os.path.join(DATA_DIR, f"{get_today()}.json")

def load_history():
    file = get_data_file()
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_history(history):
    with open(get_data_file(), "w") as f:
        json.dump(history, f)

def calc_stats(history):
    win = sum(h["amount"] for h in history if h["result"] == "win")
    lose = sum(h["amount"] for h in history if h["result"] == "lose")
    profit = win - lose
    return win, lose, profit

def get_next_bet(history):
    losses = 0
    for h in reversed(history):
        if h["date"] != get_today(): break
        if h["result"] == "lose": losses += 1
        else: break
    return GAP_THEP[losses] if losses < len(GAP_THEP) else GAP_THEP[0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = load_history()
    bet = get_next_bet(history)
    win, lose, profit = calc_stats(history)

    warn = ""
    if profit >= TARGET_PROFIT:
        warn = "
🎯 ĐÃ ĐẠT LÃI MỤC TIÊU"
    elif profit <= MAX_LOSS:
        warn = "
⚠️ CẢNH BÁO: LỖ VƯỢT MỨC"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Xem lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])
    await update.message.reply_text(
        f"📅 {get_today()}
"
        f"🎯 Cược tiếp: {bet}đ
"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ
"
        f"📈 Lời/lỗ: {profit:+}đ{warn}",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_history()
    today = get_today()

    if query.data == "win" or query.data == "lose":
        bet = get_next_bet(data)
        data.append({"date": today, "result": query.data, "amount": bet})
        save_history(data)

    elif query.data == "reset":
        save_history([])

    elif query.data == "view":
        entries = [f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']}đ" for i, h in enumerate(data)]
        msg = "\n".join(entries) if entries else "📭 Chưa có lịch sử hôm nay."
        await query.edit_message_text(f"📊 Lịch sử hôm nay:\n{msg}")
        return

    # Update
    bet = get_next_bet(data)
    win, lose, profit = calc_stats(data)
    warn = ""
    if profit >= TARGET_PROFIT:
        warn = "
🎯 ĐÃ ĐẠT LÃI MỤC TIÊU"
    elif profit <= MAX_LOSS:
        warn = "
⚠️ CẢNH BÁO: LỖ VƯỢT MỨC"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Xem lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])
    await query.edit_message_text(
        f"📅 {get_today()}
"
        f"🎯 Cược tiếp: {bet}đ
"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ
"
        f"📈 Lời/lỗ: {profit:+}đ{warn}",
        reply_markup=reply_markup
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_history()
    bet = get_next_bet(data)
    win, lose, profit = calc_stats(data)
    await update.message.reply_text(
        f"📅 {get_today()}
"
        f"🎯 Cược tiếp theo: {bet}đ
"
        f"✅ Thắng: {win}đ | ❌ Thua: {lose}đ
"
        f"📈 Lời/lỗ: {profit:+}đ"
    )

if __name__ == "__main__":
    import asyncio
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.run(app.run_polling())
