from telegram.ext import Application, CommandHandler
from datetime import datetime
import json, os

# ==== CẤU HÌNH ====
BOT_TOKEN = "8044361965:AAEe2xTU0PCmYTtH4UQj1v6z5RTkE2Jo_j4"
DATA_FOLDER = "data_logs"
GAP_THEP = [5000, 10000, 15000, 25000]
VON_BAN_DAU = 500000

# ==== HÀM XỬ LÝ ====
def get_file_path():
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(DATA_FOLDER, exist_ok=True)
    return os.path.join(DATA_FOLDER, f"{today}.json")

def load_data():
    path = get_file_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "so_du": VON_BAN_DAU,
        "von_hom_nay": VON_BAN_DAU,
        "chuoi_index": 0,
        "lich_su": []
    }

def save_data(data):
    path = get_file_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def tinh_lai(ket_qua):
    data = load_data()
    index = data.get("chuoi_index", 0)
    cuoc = GAP_THEP[index] if index < len(GAP_THEP) else GAP_THEP[0]
    if ket_qua == "win":
        lai = round(cuoc * 0.96)
        data["so_du"] += lai
        data["chuoi_index"] = 0
        data["lich_su"].append(["Thắng", cuoc, lai, data["so_du"]])
        msg = f"✅ Thắng {cuoc:,}đ ➜ +{lai:,}đ\n💰 Số dư: {data['so_du']:,}đ"
    else:
        data["so_du"] -= cuoc
        data["chuoi_index"] += 1
        if data["chuoi_index"] >= len(GAP_THEP):
            data["chuoi_index"] = 0
            msg = "⚠️ Hết chuỗi gấp thếp! Reset chuỗi."
        else:
            msg = f"❌ Thua {cuoc:,}đ ➜ -{cuoc:,}đ"
        data["lich_su"].append(["Thua", cuoc, -cuoc, data["so_du"]])
        msg += f"\n💰 Số dư: {data['so_du']:,}đ"

    save_data(data)
    return msg

# ==== BOT HANDLERS ====
async def start(update, context):
    await update.message.reply_text("🤖 Bot đã sẵn sàng!\n/start để bắt đầu\n/status để xem trạng thái\n/win hoặc /lose")

async def status(update, context):
    d = load_data()
    so_du = d["so_du"]
    von = d["von_hom_nay"]
    lai = so_du - von
    msg = f"📅 {datetime.now().strftime('%d/%m/%Y')}\n💰 Số dư: {so_du:,}đ\n📊 Lãi/lỗ: {lai:+,}đ"
    await update.message.reply_text(msg)

async def win(update, context):
    msg = tinh_lai("win")
    await update.message.reply_text(msg)

async def lose(update, context):
    msg = tinh_lai("lose")
    await update.message.reply_text(msg)

async def reset(update, context):
    save_data({
        "so_du": VON_BAN_DAU,
        "von_hom_nay": VON_BAN_DAU,
        "chuoi_index": 0,
        "lich_su": []
    })
    await update.message.reply_text("🔄 Đã reset vốn về 500,000đ.")

# ==== CHẠY BOT ====
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("win", win))
app.add_handler(CommandHandler("lose", lose))
app.add_handler(CommandHandler("reset", reset))

print("🤖 Bot Telegram chạy 24/7...")
app.run_polling()
