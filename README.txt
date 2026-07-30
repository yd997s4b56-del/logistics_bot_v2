=== ЛОГИСТИЧЕСКАЯ ПЛАТФОРМА ===

1. НАСТРОЙКА:
   Открой config.py и вставь свои токены и Telegram ID.
   Токены: @BotFather (создай 3 бота)
   Telegram ID: @userinfobot

2. ЛОКАЛЬНЫЙ ЗАПУСК:
   python3 -m pip install -r requirements.txt
   python3 main.py

3. ДЛЯ РАБОТЫ 24/7 (Render.com):
   - Залей на GitHub
   - На Render: New -> Web Service -> Python 3
   - Build: pip install -r requirements.txt
   - Start: python main.py
   - Environment Variables: CUSTOMER_BOT_TOKEN, CARRIER_BOT_TOKEN, ADMIN_BOT_TOKEN, ADMIN_IDS
   - UptimeRobot.com чтобы не засыпал (бесплатно)

4. ВАЖНО:
   В @BotFather выключи Group Privacy для всех 3 ботов (Bot Settings -> Group Privacy -> Turn OFF)

5. КОМАНДЫ АДМИНА:
   /verify 123456789 - подтвердить перевозчика
   /stats - статистика
