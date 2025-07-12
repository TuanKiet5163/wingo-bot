from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime
import os
import json

# ==== CẤU HÌNH ====
TOKEN = os.getenv("8044361965:AAHyGOUI2CaBN57r5Ogtt7RhxpYpf7V9-pc")  # Đặt biến môi trường trên Railway
VON_BAN_DAU = 500000
GAP_THEP = [5000, 10000, 20000, 40000]
DU_LIEU_FILE = "data.json"

# ==== HÀM DỮ LIỆU ====
def load_data():
    if os.path.exists(DU_LIEU_FILE):
        with open(DU_LIEU_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "so_du": VON_BAN_DAU,
        "von_hom_nay": VON_BAN_DAU,
        "chuoi_index": 0,
        "lich_su": []
    }

def save_data(data):
    with open(DU_LIEU_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_cuoc(data):
    index = data.get("chuoi_index", 0)
    return GAP_THEP[index] if index < len(GAP_THEP) else GAP_THEP[-1]

def tinh_lai(ket_qua):
    data = load_data()
    index = data.get("chuoi_index", 0)
    cuoc = GAP_THEP[index] if index < len(GAP_THEP) else GAP_THEP[-1]

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
            msg = f"❌ Thua {cuoc:,}đ ➜ -{cuoc:,}đ\n⚠️ Đã hết chuỗi gấp thếp, reset chuỗi."
        else:
            msg = f"❌ Thua {cuoc:,}đ ➜ -{cuoc:,}đ"
        data["lich_su"].append(["Thua", cuoc, -cuoc, data["so_du"]])
        msg += f"\n💰 Số dư: {data['so_du']:,}đ"

    save_data(data)
    return msg

# ==== HANDLERS ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    so_du = data["so_du"]
    von = data["von_hom_nay"]
    lai = so_du - von
    cuoc_tiep = get_next_cuoc(data)

    msg = (
        f"🎯 {datetime.now().strftime('%d/%m/%Y')}\n"
        f"💰 Số dư: {so_du:,}đ\n"
        f"📊 Lãi/Lỗ: {lai:+,}đ\n"
        f"🎲 Cược tiếp theo: {cuoc_tiep:,}đ\n"
        f"👇 Chọn hành động:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Thắng", callback_data="win"),
            InlineKeyboardButton("❌ Thua", callback_data="lose")
        ],
        [
            InlineKeyboardButton("📊 Trạng thái", callback_data="status"),
            InlineKeyboardButton("🔄 Reset tiền", callback_data="reset")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "win":
        msg = tinh_lai("win")
    elif action == "lose":
        msg = tinh_lai("lose")
    elif action == "status":
        d = load_data()
        so_du = d["so_du"]
        lai = so_du - d["von_hom_nay"]
        cuoc = get_next_cuoc(d)
        msg = (
            f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
            f"💰 Số dư: {so_du:,}đ\n"
            f"📊 Lãi/Lỗ: {lai:+,}đ\n"
            f"🎲 Cược tiếp theo: {cuoc:,}đ"
        )
    elif action == "reset":
        save_data({
            "so_du": VON_BAN_DAU,
            "von_hom_nay": VON_BAN_DAU,
            "chuoi_index": 0,
            "lich_su": []
        })
        msg = "🔄 Đã reset về vốn ban đầu: 500,000đ."

    await query.edit_message_text(msg)

# ==== KHỞI ĐỘNG ====
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
print("🤖 Bot Telegram đang chạy...")
app.run_polling()
