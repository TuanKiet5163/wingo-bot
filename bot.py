import json
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔐 Token Telegram tích hợp trực tiếp (không khuyến khích chia sẻ công khai)
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"

DATA_FILE = "data.json"

DEFAULT_DATA = {
    "balance": 500000,
    "profit": 0,
    "current_bet": 10000,
    "history": [],
    "loss_streak": 0,
    "initial_balance": 500000,
    "last_day": str(date.today())
}

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def reset_if_new_day(data):
    today = str(date.today())
    if data.get("last_day") != today:
        data["profit"] = 0
        data["history"] = []
        data["loss_streak"] = 0
        data["last_day"] = today
        data["initial_balance"] = data["balance"]
        save_data(data)

def calculate_next_bet(loss_streak):
    base = 10000
    return base * (2 ** loss_streak)

def main_menu(data):
    return (
        f"💰 Số dư: {data['balance']:,} đ\n"
        f"📉 Vốn ban đầu hôm nay: {data['initial_balance']:,} đ\n"
        f"📈 Lời/Lỗ: {data['balance'] - data['initial_balance']:+,} đ\n"
        f"🎯 Tiền cược tiếp theo: {data['current_bet']:,} đ\n"
        "\nChọn hành động:"
    )

def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Thắng", callback_data="win"),
         InlineKeyboardButton("❌ Thua", callback_data="lose")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset"),
         InlineKeyboardButton("📊 Lịch sử", callback_data="history")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    reset_if_new_day(data)
    await update.message.reply_text(main_menu(data), reply_markup=build_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    reset_if_new_day(data)

    action = query.data

    if action == "win":
        data["balance"] += data["current_bet"]
        data["profit"] += data["current_bet"]
        data["history"].append(f"[✅] +{data['current_bet']:,} đ")
        data["loss_streak"] = 0
    elif action == "lose":
        data["balance"] -= data["current_bet"]
        data["profit"] -= data["current_bet"]
        data["history"].append(f"[❌] -{data['current_bet']:,} đ")
        data["loss_streak"] += 1
    elif action == "reset":
        data = DEFAULT_DATA.copy()
        data["last_day"] = str(date.today())
    elif action == "history":
        history_text = "\n".join(data["history"][-15:]) or "Chưa có lịch sử."
        await query.edit_message_text(
            f"Lịch sử gần đây:\n{history_text}\n\n"
            f"💰 Số dư: {data['balance']:,} đ\n"
            f"📉 Vốn ban đầu hôm nay: {data['initial_balance']:,} đ\n"
            f"📈 Lời/Lỗ: {data['balance'] - data['initial_balance']:+,} đ\n"
            f"🎯 Cược tiếp theo: {data['current_bet']:,} đ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Quay lại", callback_data="back")]
            ])
        )
        save_data(data)
        return

    if action != "history":
        data["current_bet"] = calculate_next_bet(data["loss_streak"])
        save_data(data)
        await query.edit_message_text(main_menu(data), reply_markup=build_keyboard())

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot đang chạy...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
