from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os, datetime, json

# === Cấu hình ===
TOKEN = "8044361965:AAEe2xTU0PCmYTtH4UQj1v6z5RTkE2Jo_j4"
DATA_FILE = "data.json"
GAP_THEP = [5000, 10000, 15000, 25000]
SO_DU_BAN_DAU = 500000

# === Lối hỗ trợ ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "so_du": SO_DU_BAN_DAU,
        "chuoi": 0,
        "lich_su": [],
        "ngay": str(datetime.date.today()),
        "loi_nhuan": 0
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# === Xử lý lệnh ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    reply = (
        "🤖 Bot đã sẵn sàng!\n"
        "/start để bắt đầu\n/status để xem trạng thái\n"
        "/win hoặc /lose"
    )
    await update.message.reply_text(reply)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    cuoc = GAP_THEP[data["chuoi"]] if data["chuoi"] < len(GAP_THEP) else GAP_THEP[0]
    reply = (
        f"💰 Số dư: {data['so_du']:,} đ\n"
        f"🎲 Cược tiếp: {cuoc:,} đ\n"
        f"📅 Ngày: {data['ngay']}\n"
        f"📈 Lãi/lỗ: {data['loi_nhuan']:+,} đ\n"
        "\n/reset để đặt lại"
    )
    await update.message.reply_text(reply)

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if data["chuoi"] >= len(GAP_THEP): data["chuoi"] = 0
    cuoc = GAP_THEP[data["chuoi"]]
    lai = int(cuoc * 0.96)
    data["so_du"] += lai
    data["loi_nhuan"] += lai
    data["chuoi"] = 0
    data["lich_su"].append(f"Thắng {cuoc:,} ➔ +{lai:,}")
    save_data(data)
    await update.message.reply_text(f"✅ Thắng {cuoc:,} ➔ +{lai:,} đ\n💰 Số dư: {data['so_du']:,} đ")

async def lose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if data["chuoi"] >= len(GAP_THEP): data["chuoi"] = 0
    cuoc = GAP_THEP[data["chuoi"]]
    data["so_du"] -= cuoc
    data["loi_nhuan"] -= cuoc
    data["chuoi"] += 1
    data["lich_su"].append(f"Thua {cuoc:,} ➔ -{cuoc:,}")
    save_data(data)
    await update.message.reply_text(f"❌ Thua {cuoc:,} ➔ -{cuoc:,} đ\n💰 Số dư: {data['so_du']:,} đ")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    os.remove(DATA_FILE) if os.path.exists(DATA_FILE) else None
    await update.message.reply_text("🔄 Đã đặt lại vốn.")

# === Khởi chạy ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("lose", lose))
    app.add_handler(CommandHandler("reset", reset))
    app.run_polling()
