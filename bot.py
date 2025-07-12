import os, json
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

# === TOKEN đã tích hợp sẵn ===
TOKEN = "8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATTERN = [5000, 10000, 15000, 25000]
INITIAL_BALANCE = 500_000
SCHEDULE_HOUR = 23
SCHEDULE_MINUTE = 59

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

def analyze_ai_suggestion(history):
    today = [h for h in history if h["date"] == get_today()]
    total = len(today)
    losses = sum(1 for h in today if h["result"] == "lose")
    streak = lose_streak(today)
    base_bet = get_next_bet(today)
    msg = f"🧠 Gợi ý cược: {base_bet:,}đ"
    if streak >= 3 or (losses >= 5 and losses / total > 0.6):
        msg += "\n❗ Đang chuỗi thua dài\n⛔ NÊN NGHỈ!"
    elif streak == 2:
        msg += "\n⚠️ 2 thua liên tiếp – nên cược nhỏ"
    prob = round((losses / total) * 100) if total else 0
    msg += f"\n🔍 Xác suất thua hiện tại: ~{prob}%"
    return base_bet, msg

async def show_status(send_func):
    data = load_data()
    bet = get_next_bet(data["history"])
    wins, losses, profit = calc_stats(data)
    time = get_now_time()
    _, ai_msg = analyze_ai_suggestion(data["history"])
    warn = ""
    if profit >= 100_000: warn += "\n🎯 ĐẠT MỤC TIÊU LÃI"
    if profit <= -150_000: warn += "\n⚠️ LỖ VƯỢT NGƯỠNG"
    if lose_streak(data["history"]) >= 3: warn += "\n❗ THUA LIÊN TIẾP"

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="win"),
         InlineKeyboardButton("❌ LOSE", callback_data="lose")],
        [InlineKeyboardButton("📊 Lịch sử", callback_data="view"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])

    await send_func(
        f"📅 {get_today()} | 🕒 {time}\n"
        f"💰 Số dư: {data['balance']:,}đ\n"
        f"🎯 Cược tiếp: {bet:,}đ\n"
        f"✅ Thắng: {wins:,}đ | ❌ Thua: {losses:,}đ\n"
        f"📈 Lãi/Lỗ: {profit:+,}đ{warn}\n\n{ai_msg}",
        reply_markup=markup
    )

def create_summary_chart(data):
    history = [h for h in data["history"] if h["date"] == get_today()]
    if not history: return None
    times = list(range(1, len(history)+1))
    profits = []
    current = INITIAL_BALANCE
    for h in history:
        change = round(h["amount"] * 0.96) if h["result"] == "win" else -h["amount"]
        current += change
        profits.append(current - INITIAL_BALANCE)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(times, profits, marker='o')
    ax1.set_title("Biểu đồ Lãi/Lỗ")
    ax1.set_xlabel("Ván")
    ax1.set_ylabel("Lời/Lỗ (đ)")

    win = sum(1 for h in history if h["result"] == "win")
    lose = sum(1 for h in history if h["result"] == "lose")
    ax2.pie([win, lose], labels=["WIN", "LOSE"], autopct="%1.0f%%", colors=["green", "red"])
    ax2.set_title("Tỷ lệ WIN/LOSE")

    img_path = os.path.join(DATA_DIR, "chart.png")
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    return img_path

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    wins, losses, profit = calc_stats(data)
    total = len(data["history"])
    msg = (
        f"📊 TỔNG KẾT {get_today()}:\n"
        f"🎮 Số phiên: {total}\n"
        f"✅ Tổng thắng: {wins:,}đ\n"
        f"❌ Tổng thua: {losses:,}đ\n"
        f"📈 Lời/Lỗ: {profit:+,}đ"
    )
    await update.message.reply_text(msg)

    chart_path = create_summary_chart(data)
    if chart_path:
        await update.message.reply_photo(InputFile(chart_path))

    await update.message.reply_document(InputFile(get_file()))

async def auto_von(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        von = int(context.args[0])
        so_van = int(context.args[1]) if len(context.args) > 1 else 8
        goiy = round(von / so_van)
        data = load_data()
        data["balance"] = von
        save_data(data)
        await update.message.reply_text(f"✅ Đặt vốn: {von:,}đ để chơi {so_van} ván.\n🎯 Gợi ý: {goiy:,}đ mỗi ván.")
    except:
        await update.message.reply_text("❌ Sai cú pháp.\nVí dụ: /auto_von 100000 10")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_document(InputFile(get_file()))

async def resetvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["balance"] = INITIAL_BALANCE
    save_data(data)
    await update.message.reply_text("🔁 Reset vốn về 500.000đ.")
    await show_status(update.message.reply_text)

async def setvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        data = load_data()
        data["balance"] = amount
        save_data(data)
        await update.message.reply_text(f"✅ Đặt lại vốn: {amount:,}đ")
    except:
        await update.message.reply_text("❌ Dùng: /setvon 200000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update.message.reply_text)

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
            await query.edit_message_text("📭 Chưa có lịch sử.")
            return
        lines = [f"{i+1}. {'✅' if h['result']=='win' else '❌'} {h['amount']:,}đ" for i, h in enumerate(history)]
        await query.edit_message_text("📊 Lịch sử hôm nay:\n" + "\n".join(lines[-15:]))
        return

    if query.data in ["win", "lose"]:
        bet = get_next_bet(history)
        if bet > balance and query.data == "lose":
            await query.edit_message_text("❌ Không đủ vốn. Dùng /setvon hoặc /resetvon")
            return
        amount = round(bet * 0.96) if query.data == "win" else -bet
        balance += amount
        history.append({"date": get_today(), "result": query.data, "amount": bet})
        data["balance"] = balance
        data["history"] = history
        save_data(data)

    await show_status(query.edit_message_text)

# ===== SCHEDULER: gửi tổng kết lúc 23:59 =====
async def auto_summary():
    class FakeMsg:
        async def reply_text(self, msg): pass
        async def reply_document(self, file): pass
        async def reply_photo(self, file): pass
    await summary(Update(update_id=0, message=FakeMsg()), None)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("resetvon", resetvon))
    app.add_handler(CommandHandler("setvon", setvon))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("auto_von", auto_von))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CallbackQueryHandler(button))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(auto_summary()), "cron", hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE)
    scheduler.start()

    print("🤖 Bot đang chạy...")
    asyncio.run(app.run_polling())
