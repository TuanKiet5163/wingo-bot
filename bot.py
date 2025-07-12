from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os, datetime, json

# === Cấu hình ===
TOKEN = "<8044361965:AAEe2xTU0PCmYTtH4UQj1v6z5RTkE2Jo_j4>"
DATA_FILE = "data.json"
GAP_THEP = [5000, 10000, 15000, 25000]
SO_DU_BAN_DAU = 500000

# === Lỗi hỗ trợ ===
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
        "\U0001F916 Bot đã sẵn sàng!\n"
        "/start để bắt đầu\n"
        "/status để xem trạng thái\n"
        "/win hoặc /lose"
    )
    await update.message.reply_text(reply)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    cuoc = GAP_THEP[data["chuoi"]]
    tong_loi = data["so_du"] - SO_DU_BAN_DAU
    await update.message.reply_text(
        f"\U0001F4B0 Số dư: {data['so_du']:,} đ\n"
        f"\U0001F3B2 Cược tiếp: {cuoc:,} đ\n"
        f"\U0001F4C8 Lãi/Lỗ: {tong_loi:+,} đ"
    )

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    cuoc = GAP_THEP[data["chuoi"]]
    lai = round(cuoc * 0.96)
    data["so_du"] += lai
    data["lich_su"].append(("Thắng", cuoc, lai, data["so_du"]))
    data["chuoi"] = 0
    save_data(data)
    await update.message.reply_text(
        f"\u2705 Thắng {cuoc:,} ➔ +{lai:,} đ\n\U0001F4B0 Số dư: {data['so_du']:,} đ"
    )

async def lose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    cuoc = GAP_THEP[data["chuoi"]]
    data["so_du"] -= cuoc
    data["lich_su"].append(("Thua", cuoc, -cuoc, data["so_du"]))
    data["chuoi"] += 1
    if data["chuoi"] >= len(GAP_THEP):
        data["chuoi"] = 0
    save_data(data)
    await update.message.reply_text(
        f"\u274C Thua {cuoc:,} ➔ -{cuoc:,} đ\n\U0001F4B0 Số dư: {data['so_du']:,} đ"
    )

# === Khởi chạy bot ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("lose", lose))

    app.run_polling()
