import asyncio
import os
import logging
from aiohttp import web
from customer_bot import create_customer_app
from carrier_bot import create_carrier_app
from admin_bot import create_admin_app
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health(request):
    return web.Response(text="✅ Боты работают 24/7!")

async def run_web():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web-сервер на порту {port}")

async def run_bot(app, name):
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        me = await app.bot.get_me()
        logger.info(f"✅ Бот @{me.username} запущен!")
        # Держим живым
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"❌ Ошибка в боте {name}: {e}")
        raise

async def main():
    init_db()
    await run_web()

    c_app = create_customer_app()
    r_app = create_carrier_app()
    a_app = create_admin_app()

    await asyncio.gather(
        run_bot(c_app, "Customer"),
        run_bot(r_app, "Carrier"),
        run_bot(a_app, "Admin")
    )

if __name__ == '__main__':
    asyncio.run(main())
