import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from config import CUSTOMER_BOT_TOKEN, ADMIN_IDS
from database import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REG_NAME, REG_PHONE, MENU = range(3)
F_CITY, F_ADDR, T_CITY, T_ADDR, CARGO, WEIGHT, VOLUME, PRICE = range(3, 11)
D_TYPE, D_VAL = range(11, 13)

def menu_kb():
    return ReplyKeyboardMarkup([["📝 Новая заявка","📋 Мои заявки"],["📞 Поддержка"]], resize_keyboard=True)

def phone_kb():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Отправить номер", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    c = get_customer(uid)
    if c:
        await update.message.reply_text("👋 Снова здравствуйте, " + c['full_name'] + "!", reply_markup=menu_kb())
        return MENU
    await update.message.reply_text("👋 Добро пожаловать! Введите ФИО:")
    return REG_NAME

async def reg_name(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['fn'] = update.message.text
    await update.message.reply_text("Отправьте номер телефона:", reply_markup=phone_kb())
    return REG_PHONE

async def reg_phone(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    add_customer(u.id, u.username, update.message.contact.phone_number, context.user_data['fn'])
    await update.message.reply_text("✅ Регистрация завершена!", reply_markup=menu_kb())
    return MENU

async def new_order(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Шаг 1/8: Город отправления:")
    return F_CITY

async def f_city(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['fc'] = update.message.text
    await update.message.reply_text("Шаг 2/8: Базовый адрес отправления (улица, район):")
    return F_ADDR

async def f_addr(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['fa'] = update.message.text
    await update.message.reply_text("Шаг 3/8: Город назначения:")
    return T_CITY

async def t_city(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['tc'] = update.message.text
    await update.message.reply_text("Шаг 4/8: Базовый адрес назначения:")
    return T_ADDR

async def t_addr(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['ta'] = update.message.text
    await update.message.reply_text("Шаг 5/8: Тип груза:")
    return CARGO

async def cargo(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['cg'] = update.message.text
    await update.message.reply_text("Шаг 6/8: Вес (кг):")
    return WEIGHT

async def weight(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['wt'] = update.message.text
    await update.message.reply_text("Шаг 7/8: Объем (m3):")
    return VOLUME

async def volume(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data['vl'] = update.message.text
    await update.message.reply_text("Шаг 8/8: Желаемая цена (тенге):")
    return PRICE

async def price(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(' ','').replace('₸',''))
    except:
        await update.message.reply_text("❌ Введите число:")
        return PRICE
    uid = update.effective_user.id
    oid = create_order(uid, context.user_data['fc'], context.user_data['fa'],
                       context.user_data['tc'], context.user_data['ta'],
                       context.user_data['cg'], context.user_data['wt'], context.user_data['vl'], price)
    for aid in ADMIN_IDS:
        try:
            msg = "🆕 Заявка #" + str(oid) + "!" + "
" + "📍 " + context.user_data['fc'] + " → " + context.user_data['tc'] + "
" + "📦 " + context.user_data['cg'] + "
" + "💰 " + str(price) + " ₸"
            await context.bot.send_message(aid, msg)
        except: pass
    await update.message.reply_text("✅ Заявка #" + str(oid) + " создана! После принятия перевозчиком вы сможете уточнить детали.", reply_markup=menu_kb())
    for k in ['fc','fa','tc','ta','cg','wt','vl']: context.user_data.pop(k,None)
    return MENU

async def my_orders(update:Update, context:ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    orders = get_customer_orders(uid)
    if not orders:
        await update.message.reply_text("У вас нет заявок.", reply_markup=menu_kb())
        return
    for o in orders:
        em = {'new':'🆕 Новая','accepted':'✅ Принят','in_progress':'🚛 В пути','completed':'✔️','cancelled':'❌'}.get(o['status'],o['status'])
        lines = [
            "📦 #" + str(o['order_id']),
            "📍 " + o['from_city'] + " → " + o['to_city'],
            "📦 " + o['cargo_type'] + " | ⚖️ " + o['weight'] + " | 📐 " + o['volume'],
            "💰 " + str(o['price']) + " ₸",
            "Статус: " + em
        ]
        if o['carrier_id']:
            lines.append("🚛 Перевозчик назначен")
        txt = "
".join(lines)
        kb = []
        if o['status'] in ('accepted','in_progress'):
            kb.append([InlineKeyboardButton("➕ Добавить детали", callback_data="d_" + str(o['order_id']))])
        kb.append([InlineKeyboardButton("📋 Детали", callback_data="v_" + str(o['order_id']))])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def add_d_cb(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data['d_oid'] = int(q.data.split('_')[1])
    await q.edit_message_text("Что уточнить?
1. Точный адрес подачи
2. Точный адрес доставки
3. Время подачи
4. Контактное лицо
5. Примечания

Введите номер или название:")
    return D_TYPE

async def d_type(update:Update, context:ContextTypes.DEFAULT_TYPE):
    t = update.message.text.lower()
    m = {'1':'Точный адрес подачи','2':'Точный адрес доставки','3':'Время подачи','4':'Контактное лицо','5':'Примечания'}
    context.user_data['dt'] = m.get(t, t)
    await update.message.reply_text("Введите детали для '" + context.user_data['dt'] + "':")
    return D_VAL

async def d_val(update:Update, context:ContextTypes.DEFAULT_TYPE):
    oid = context.user_data['d_oid']
    add_detail(oid, context.user_data['dt'], update.message.text, 'customer')
    for aid in ADMIN_IDS:
        try:
            msg = "📝 Детали к #" + str(oid) + "
" + "Тип: " + context.user_data['dt'] + "
" + "Значение: " + update.message.text
            await context.bot.send_message(aid, msg)
        except: pass
    await update.message.reply_text("✅ Детали добавлены! Админ передаст перевозчику.", reply_markup=menu_kb())
    context.user_data.pop('d_oid',None)
    context.user_data.pop('dt',None)
    return MENU

async def view_cb(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = int(q.data.split('_')[1])
    o = get_order(oid)
    d = get_details(oid)
    lines = [
        "📦 #" + str(oid),
        "🚚 Откуда: " + o['from_city'] + ", " + o['from_address'],
        "🏁 Куда: " + o['to_city'] + ", " + o['to_address']
    ]
    if d:
        lines.append("")
        lines.append("📋 Доп. детали:")
        for x in d:
            lines.append("• " + x['detail_type'] + ": " + x['detail_value'])
    else:
        lines.append("")
        lines.append("📋 Деталей пока нет.")
    await q.edit_message_text("
".join(lines))

async def support(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите вопрос:", reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True))

async def menu_h(update:Update, context:ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "📝 Новая заявка":
        await update.message.reply_text("📝 Шаг 1/8: Город отправления:")
        return F_CITY
    elif t == "📋 Мои заявки":
        await my_orders(update, context)
        return MENU
    elif t == "📞 Поддержка":
        await support(update, context)
        return MENU
    elif t == "🔙 Назад":
        await update.message.reply_text("Меню:", reply_markup=menu_kb())
        return MENU
    else:
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid, "💬 От заказчика " + str(update.effective_user.id) + ":" + "
" + t)
            except: pass
        await update.message.reply_text("✉️ Отправлено администратору.")
        return MENU

def create_customer_app():
    init_db()
    app = Application.builder().token(CUSTOMER_BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.CONTACT, reg_phone)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_h)],
            F_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, f_city)],
            F_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, f_addr)],
            T_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, t_city)],
            T_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, t_addr)],
            CARGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, cargo)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
            VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            D_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_type)],
            D_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_val)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(add_d_cb, pattern=r'^d_\d+$'))
    app.add_handler(CallbackQueryHandler(view_cb, pattern=r'^v_\d+$'))
    return app
