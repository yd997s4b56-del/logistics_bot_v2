import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                phone TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS carriers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                phone TEXT,
                full_name TEXT,
                vehicle_type TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                from_city TEXT,
                from_address TEXT,
                to_city TEXT,
                to_address TEXT,
                cargo_type TEXT,
                weight TEXT,
                volume TEXT,
                price INTEGER,
                status TEXT DEFAULT 'new',
                carrier_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                completed_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                detail_type TEXT,
                detail_value TEXT,
                added_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def add_customer(user_id, username, phone, full_name):
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?)",
                   (user_id, username, phone, full_name, datetime.now()))

def get_customer(user_id):
    with get_db() as db:
        return db.execute("SELECT * FROM customers WHERE user_id=?", (user_id,)).fetchone()

def add_carrier(user_id, username, phone, full_name, vehicle_type):
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO carriers VALUES (?,?,?,?,?,?,?)",
                   (user_id, username, phone, full_name, vehicle_type, 0, datetime.now()))

def get_carrier(user_id):
    with get_db() as db:
        return db.execute("SELECT * FROM carriers WHERE user_id=?", (user_id,)).fetchone()

def verify_carrier(user_id):
    with get_db() as db:
        db.execute("UPDATE carriers SET is_verified=1 WHERE user_id=?", (user_id,))

def create_order(cid, fc, fa, tc, ta, cargo, w, v, price):
    with get_db() as db:
        cur = db.execute("""
            INSERT INTO orders (customer_id,from_city,from_address,to_city,to_address,cargo_type,weight,volume,price,status)
            VALUES (?,?,?,?,?,?,?,?,?,'new')
        """, (cid, fc, fa, tc, ta, cargo, w, v, price))
        return cur.lastrowid

def get_order(oid):
    with get_db() as db:
        return db.execute("SELECT * FROM orders WHERE order_id=?", (oid,)).fetchone()

def get_active_orders():
    with get_db() as db:
        return db.execute("""
            SELECT o.*, c.full_name as customer_name 
            FROM orders o JOIN customers c ON o.customer_id=c.user_id 
            WHERE o.status='new' ORDER BY o.created_at DESC
        """).fetchall()

def get_carrier_orders(carrier_id):
    with get_db() as db:
        return db.execute("""
            SELECT o.*, c.full_name as customer_name
            FROM orders o JOIN customers c ON o.customer_id=c.user_id
            WHERE o.carrier_id=? AND o.status IN ('accepted','in_progress')
            ORDER BY o.created_at DESC
        """, (carrier_id,)).fetchall()

def get_customer_orders(customer_id):
    with get_db() as db:
        return db.execute("""
            SELECT o.*, car.full_name as carrier_name
            FROM orders o LEFT JOIN carriers car ON o.carrier_id=car.user_id
            WHERE o.customer_id=? ORDER BY o.created_at DESC
        """, (customer_id,)).fetchall()

def accept_order(order_id, carrier_id):
    with get_db() as db:
        db.execute("UPDATE orders SET status='accepted',carrier_id=?,accepted_at=? WHERE order_id=? AND status='new'",
                   (carrier_id, datetime.now(), order_id))

def update_status(order_id, status):
    with get_db() as db:
        db.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))

def add_detail(order_id, dtype, dval, added_by):
    with get_db() as db:
        db.execute("INSERT INTO order_details (order_id,detail_type,detail_value,added_by) VALUES (?,?,?,?)",
                   (order_id, dtype, dval, added_by))

def get_details(order_id):
    with get_db() as db:
        return db.execute("SELECT * FROM order_details WHERE order_id=? ORDER BY created_at", (order_id,)).fetchall()
