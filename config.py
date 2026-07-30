import os

CUSTOMER_BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "8887217671:AAE42e2pv660dVWw9T8fhHusRXfR4JCyoFU")
CARRIER_BOT_TOKEN = os.environ.get("CARRIER_BOT_TOKEN", "8818039393:AAEsMzLQugoj4LIK6hpWhOUPaXFvD3eHDDU")
ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN", "8974200612:AAEgnMEaDDDFwxH9w-XhupfvQSigo9rZ0F4")

raw = os.environ.get("ADMIN_IDS", "5522811632")
ADMIN_IDS = [int(x) for x in raw.split(",") if x.strip().isdigit()]

DB_PATH = "logistics.db"
