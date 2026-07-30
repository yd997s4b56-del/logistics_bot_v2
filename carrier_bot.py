import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from config import CARRIER_BOT_TOKEN, ADMIN_IDS
from database import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

C_NAME, C_PHONE, C_VEHICLE, C_MENU = range(4)

def c_menu_kb():
    return ReplyKeyboardMarkup([["📋 Заказы","🚛 Мои заказы"],["📞 Поддержка"]], resize_keyboard=True)

def c_phone_kb():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Отправить номер", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)

async def c_start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    c = get_carrier(uid)
    if c and c['is_verified']:
        await update.message.reply_text(f"👋 {c['full_name']}!
🚛 {c['vehicle_type']}", reply_markup=c_menu_kb())
        return C_MENU
    elif c and not c['is_verified']:
        await update.message.reply_text("⏳ Регистрация на проверке.")
        return ConversationHandler.END
    await update.message.reply_text("👋 Введите ФИО:")
    return C_NAME

async def c_name(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['fn'] = update.message.text
    await update.message.reply_text("Отправьте номер:", reply_markup=c_phone_kb())
    return C_PHONE

async def c_phone(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['ph'] = update.message.contact.phone_number
    await update.message.reply_text("Транспорт? (например: Фура 20т)")
    return C_VEHICLE

async def c_vehicle(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    add_carrier(u.id, u.username, context.user_data['ph'], context.user_data['fn'], update.message.text)
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"🚛 Новый перевозчик!
Имя: {context.user_data['fn']}
Тел: {context.user_data['ph']}
Транспорт: {update.message.text}
ID: {u.id}
/verify {u.id}")
        except: pass
    await update.message.reply_text("✅ Отправлено на проверку.")
    return ConversationHandler.END

async def available_orders(update:Update, context:ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if not orders:
        await update.message.reply_text("😕 Нет заказов.", reply_markup=c_menu_kb())
        return
    for o in orders:
        txt = f"📦 #{o['order_id']}
📍 {o['from_city']} → {o['to_city']}
📦 {o['cargo_type']}
⚖️ {o['weight']} | 📐 {o['volume']}
💰 {o['price']:,} ₸

⚠️ Контакты заказчика скрыты. Будут доступны после принятия."
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Принять", callback_data=f"a_{o['order_id']}")]]))

async def accept_cb(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    oid = int(q.data.split('_')[1]); cid = update.effective_user.id
    o = get_order(oid)
    if not o or o['status'] != 'new':
        await q.edit_message_text("❌ Заказ недоступен.")
        return
    accept_order(oid, cid)
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"🚛 #{oid} принят перевозчиком {cid}!")
        except: pass
    await q.edit_message_text("✅ Заказ принят! Админ передаст детали. Проверьте '🚛 Мои заказы'.")

async def my_orders_c(update:Update, context:ContextTypes.DEFAULT_TYPE):
    cid = update.effective_user.id
    orders = get_carrier_orders(cid)
    if not orders:
        await update.message.reply_text("Нет активных заказов.", reply_markup=c_menu_kb())
        return
    for o in orders:
        d = get_details(o['order_id'])
        txt = f"📦 #{o['order_id']}
📍 {o['from_city']} → {o['to_city']}
📦 {o['cargo_type']}
💰 {o['price']:,} ₸

"
        if d:
            txt += "📋 Детали:
"
            for x in d: txt += f"• {x['detail_type']}: {x['detail_value']}
"
        else: txt += "⏳ Детали ещё не добавлены.
"
        txt += "
📞 По вопросам к админу."
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Завершить", callback_data=f"x_{o['order_id']}")]]))

async def complete_cb(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    oid = int(q.data.split('_')[1])
    update_status(oid, 'completed')
    await q.edit_message_text("✅ Доставка выполнена!")
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"✅ #{oid} выполнен!")
        except: pass

async def c_support(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите вопрос:", reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True))

async def c_menu_h(update:Update, context:ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "📋 Заказы": await available_orders(update, context); return C_MENU
    elif t == "🚛 Мои заказы": await my_orders_c(update, context); return C_MENU
    elif t == "📞 Поддержка": await c_support(update, context); return C_MENU
    elif t == "🔙 Назад": await update.message.reply_text("Меню:", reply_markup=c_menu_kb()); return C_MENU
    else:
        for aid in ADMIN_IDS:
            try: await context.bot.send_message(aid, f"💬 От перевозчика {update.effective_user.id}:
{t}")
            except: pass
        await update.message.reply_text("✉️ Отправлено админу.")
        return C_MENU

def create_carrier_app():
    init_db()
    app = Application.builder().token(CARRIER_BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', c_start)],
        states={
            C_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_name)],
            C_PHONE: [MessageHandler(filters.CONTACT, c_phone)],
            C_VEHICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_vehicle)],
            C_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_menu_h)],
        },
        fallbacks=[CommandHandler('start', c_start)]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(accept_cb, pattern=r'^a_\d+$'))
    app.add_handler(CallbackQueryHandler(complete_cb, pattern=r'^x_\d+$'))
    return app
