=== ЛОГИСТИЧЕСКАЯ ПЛАТФОРМА ===

1. УСТАНОВКА (один раз):
   cd logistics_bot
   python3 -m pip install -r requirements.txt

2. НАСТРОЙКА:
   Открой config.py и вставь свои токены и Telegram ID.
   Токены получи у @BotFather (создай 3 бота).
   Telegram ID узнай у @userinfobot.

3. ЗАПУСК:
   python3 main.py

   Должно появиться:
   🌐 Web-сервер на порту 8080
   ✅ Бот @... запущен!
   ✅ Бот @... запущен!
   ✅ Бот @... запущен!

4. ВАЖНО — ВКЛЮЧИТЬ БОТОВ:
   Напиши @BotFather -> выбери бота -> Bot Settings -> Group Privacy -> Turn OFF
   (иначе бот не видит сообщения)

5. ДЛЯ РАБОТЫ 24/7 (Mac выключен):
   Залей на Render.com:
   - Зарегистрируйся на github.com
   - Загрузи эту папку как новый репозиторий
   - На Render.com: New -> Web Service -> подключи GitHub
   - Build: pip install -r requirements.txt
   - Start: python main.py
   - Добавь Environment Variables: CUSTOMER_BOT_TOKEN, CARRIER_BOT_TOKEN, ADMIN_BOT_TOKEN, ADMIN_IDS
   - Добавь UptimeRobot.com чтобы бот не засыпал (бесплатно)

=== КОМАНДЫ АДМИНА ===
/verify 123456789 — подтвердить перевозчика
/stats — статистика
