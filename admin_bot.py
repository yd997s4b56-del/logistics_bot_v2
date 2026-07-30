import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import ADMIN_BOT_TOKEN, ADMIN_IDS
from database import init_db, verify_carrier
import sqlite3
from database import DB_PATH

logging.basicConfig(level=logging.INFO)

async def verify_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Нет доступа.")
        return
    try:
        cid = int(context.args[0])
        verify_carrier(cid)
        await update.message.reply_text(f"✅ Перевозчик {cid} подтверждён!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}
Использование: /verify 123456789")

async def stats_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    customers = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    carriers = c.execute("SELECT COUNT(*) FROM carriers").fetchone()[0]
    orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    active = c.execute("SELECT COUNT(*) FROM orders WHERE status='new'").fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 Статистика:
👥 Заказчиков: {customers}
🚛 Перевозчиков: {carriers}
📦 Заказов: {orders}
🆕 Активных: {active}")

def create_admin_app():
    init_db()
    app = Application.builder().token(ADMIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler('verify', verify_cmd))
    app.add_handler(CommandHandler('stats', stats_cmd))
    return app
