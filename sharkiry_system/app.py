 from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sharkiry-2026')

DB = os.path.join(os.path.dirname(__file__), 'sharkiry.db')

USERS = {'admin': 'sharkiry2026', 'marcom': 'sharkiry2026', 'staff': 'staff1234'}
CHANNELS = ['Line OA', 'Facebook', 'Instagram', 'TikTok Shop', 'Shopee', 'เว็บไซต์', 'อื่น ๆ']
STATUSES = [
    ('pending',   'รอชำระเงิน'),
    ('confirmed', 'ยืนยันแล้ว'),
    ('packing',   'กำลังแพ็ค'),
    ('shipped',   'ส่งแล้ว'),
    ('done',      'เสร็จสิ้น'),
    ('cancelled', 'ยกเลิก'),
]
STATUS_DICT = dict(STATUSES)

# ── DB ──────────────────────────────────────────────────────────────────────
def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with get_db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            price REAL NOT NULL DEFAULT 0,
            cost  REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            low_alert INTEGER NOT NULL DEFAULT 10,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            social TEXT,
            phone TEXT,
            email TEXT,
            channel TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            customer_id INTEGER REFERENCES customers(id),
            customer_name TEXT,
            channel TEXT DEFAULT 'Line OA',
            status TEXT DEFAULT 'pending',
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            shipping REAL DEFAULT 0,
            total    REAL DEFAULT 0,
            tracking TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER REFERENCES orders(id),
            product_id  INTEGER REFERENCES products(id),
            product_name TEXT,
            qty         INTEGER DEFAULT 1,
            unit_price  REAL,
            total       REAL
        );
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT NOT NULL,
            source TEXT,
            status TEXT DEFAULT 'new',
            budget REAL DEFAULT 0,
            notes  TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS stock_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id),
            qty_change INTEGER,
            reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            budget    REAL DEFAULT 0,
            ad_spend  REAL DEFAULT 0,
            revenue   REAL DEFAULT 0,
            orders_count INTEGER DEFAULT 0,
            reach     INTEGER DEFAULT 0,
            status    TEXT DEFAULT 'active',
            start_date TEXT,
            end_date   TEXT,
            notes      TEXT,
            post_report TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        if c.execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
            c.executemany(
                'INSERT INTO products (name,sku,price,cost,stock,low_alert) VALUES (?,?,?,?,?,?)',
                [
                    ('Sharkiry Plus (1 กล่อง)',      'SKP-001', 1200,  450, 150, 20),
                    ('Sharkiry Original (1 กล่อง)',  'SKO-001',  990,  380,  80, 15),
                    ('Sharkiry Plus Bundle 3 กล่อง', 'SKP-003', 3200, 1350,  50, 10),
                    ('Sharkiry Plus Bundle 6 กล่อง', 'SKP-006', 6000, 2700,  25,  5),
                ]
            )
            c.executemany(
                'INSERT INTO customers (name,social,phone,channel) VALUES (?,?,?,?)',
                [
                    ('คุณมาลี สุขใจ',      '@maleesuk',    '081-xxx-1001', 'Line OA'),
                    ('คุณสมชาย ดีมาก',    '@somchai_d',   '082-xxx-1002', 'Facebook'),
                    ('คุณปาริชาต เพชรดี', '@parichat_p',  '088-xxx-1008', 'Line OA'),
                    ('คุณธนวัฒน์ มั่งมี', '@tanawat_m',   '090-xxx-1010', 'Instagram'),
                ]
            )
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = c.execute('''INSERT INTO orders (order_no,customer_id,customer_name,channel,status,subtotal,total,created_at,updated_at)
                         VALUES ('SK-20260619-0001',1,'คุณมาลี สุขใจ','Line OA','confirmed',3200,3200,?,?)''', (today, today))
            oid = cur.lastrowid
            c.execute('INSERT INTO order_items VALUES (NULL,?,?,?,?,?,?)',
                      (oid, 3, 'Sharkiry Plus Bundle 3 กล่อง', 1, 3200, 3200))
            cur2 = c.execute('''INSERT INTO orders (order_no,customer_id,customer_name,channel,status,subtotal,total,created_at,updated_at)
                         VALUES ('SK-20260619-0002',2,'คุณสมชาย ดีมาก','Facebook','pending',1200,1200,?,?)''', (today, today))
            oid2 = cur2.lastrowid
            c.execute('INSERT INTO order_items VALUES (NULL,?,?,?,?,?,?)',
                      (oid2, 1, 'Sharkiry Plus (1 กล่อง)', 1, 1200, 1200))
            c.execute('''INSERT INTO campaigns (name,budget,ad_spend,revenue,orders_count,reach,status,start_date,end_date)
                         VALUES ('Summer Health Boost',120000,85000,224400,187,52000,'active','2026-06-01','2026-06-30')''')
            c.executemany(
                'INSERT INTO leads (name,source,status,budget,notes) VALUES (?,?,?,?,?)',
                [
                    ('คุณแพรว อินทร์ดี',  'Facebook', 'new',       1200, 'สนใจ Sharkiry Plus'),
                    ('คุณนุสรา พวงทอง',  'Line OA',  'interested', 3600, 'ต้องการ 3 กล่อง'),
                    ('คุณชาตรี วงศ์ทอง', 'Instagram','won',        2400, 'ปิดการขายแล้ว ✦'),
                ]
            )

init_db()

# ── HELPERS ─────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def next_order_no():
    prefix = 'SK-' + datetime.now().strftime('%Y%m%d') + '-'
    with get_db() as c:
        last = c.execute(
            "SELECT order_no FROM orders WHERE order_no LIKE ? ORDER BY id DESC LIMIT 1",
            (prefix + '%',)
        ).fetchone()
    seq = int(last['order_no'].split('-')[-1]) + 1 if last else 1
    return prefix + str(seq).zfill(4)

def days_since(dt_str):
    try:
        dt = datetime.strptime(dt_str[:10], '%Y-%m-%d')
        return (datetime.now() - dt).days
    except:
        return 0

def fmt_thb(n):
    try:
        return f'฿{float(n):,.0f}'
    except:
        return '฿0'

app.jinja_env.globals.update(
    fmt_thb=fmt_thb,
    days_since=days_since,
    STATUS_DICT=STATUS_DICT,
    CHANNELS=CHANNELS,
    STATUSES=STATUSES,
    now=datetime.now,
)

# ── AUTH ────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username', ''), request.form.get('password', '')
        if USERS.get(u) == p:
            session['user'] = u
            return redirect(url_for('dashboard'))
        flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    with get_db() as c:
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')

        today_orders  = c.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at)=? AND status!='cancelled'", (today,)).fetchone()[0]
        today_revenue = c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE DATE(created_at)=? AND status!='cancelled'", (today,)).fetchone()[0]
        month_revenue = c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE strftime('%Y-%m',created_at)=? AND status!='cancelled'", (month,)).fetchone()[0]
        pending_count = c.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0]
        low_stock     = c.execute("SELECT * FROM products WHERE stock<=low_alert AND active=1").fetchall()
        recent_orders = c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 8").fetchall()

        # 6-month revenue for chart
        months_data = []
        for i in range(5, -1, -1):
            d = datetime.now().replace(day=1) - timedelta(days=i*28)
            m = d.strftime('%Y-%m')
            rev = c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE strftime('%Y-%m',created_at)=? AND status!='cancelled'", (m,)).fetchone()[0]
            months_data.append({'month': d.strftime('%b %Y'), 'revenue': rev})

        total_customers = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        churn_count = 0
        all_custs = c.execute('''
            SELECT c.id, MAX(o.created_at) as last_order
            FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.status!='cancelled'
            GROUP BY c.id''').fetchall()
        for cu in all_custs:
            if cu['last_order'] and days_since(cu['last_order']) > 45:
                churn_count += 1

    return render_template('dashboard.html',
        today_orders=today_orders, today_revenue=today_revenue,
        month_revenue=month_revenue, pending_count=pending_count,
        low_stock=low_stock, recent_orders=recent_orders,
        months_data=months_data, total_customers=total_customers,
        churn_count=churn_count)

# ── ORDERS ───────────────────────────────────────────────────────────────────
@app.route('/orders')
@login_required
def orders():
    status_f  = request.args.get('status', '')
    channel_f = request.args.get('channel', '')
    search    = request.args.get('q', '')
    with get_db() as c:
        q = "SELECT * FROM orders WHERE 1=1"
        params = []
        if status_f:
            q += " AND status=?"; params.append(status_f)
        if channel_f:
            q += " AND channel=?"; params.append(channel_f)
        if search:
            q += " AND (customer_name LIKE ? OR order_no LIKE ?)"; params += [f'%{search}%', f'%{search}%']
        q += " ORDER BY created_at DESC"
        order_list = c.execute(q, params).fetchall()
    return render_template('orders.html', orders=order_list,
                           status_f=status_f, channel_f=channel_f, search=search)

@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
def order_new():
    if request.method == 'POST':
        f = request.form
        cust_id   = f.get('customer_id') or None
        cust_name = f.get('customer_name', '').strip()
        channel   = f.get('channel', 'Line OA')

        # Auto-create customer if needed
        if not cust_id and cust_name:
            with get_db() as c:
                cur = c.execute('INSERT INTO customers (name,social,phone,channel) VALUES (?,?,?,?)',
                          (cust_name, f.get('social',''), f.get('phone',''), channel))
                cust_id = cur.lastrowid

        pids   = request.form.getlist('product_id[]')
        qtys   = request.form.getlist('qty[]')
        prices = request.form.getlist('price[]')

        subtotal = sum(float(p) * int(q) for p, q in zip(prices, qtys) if p and q)
        discount = float(f.get('discount', 0) or 0)
        shipping = float(f.get('shipping', 0) or 0)
        total    = subtotal - discount + shipping
        order_no = next_order_no()
        now      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with get_db() as c:
            cur = c.execute('''INSERT INTO orders
                (order_no,customer_id,customer_name,channel,status,subtotal,discount,shipping,total,notes,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                (order_no, cust_id, cust_name, channel, 'pending',
                 subtotal, discount, shipping, total, f.get('notes',''), now, now))
            oid = cur.lastrowid

            for pid, qty, price in zip(pids, qtys, prices):
                if pid and qty:
                    prod = c.execute('SELECT name FROM products WHERE id=?', (pid,)).fetchone()
                    pname = prod['name'] if prod else ''
                    line_total = float(price) * int(qty)
                    c.execute('INSERT INTO order_items VALUES (NULL,?,?,?,?,?,?)',
                              (oid, pid, pname, int(qty), float(price), line_total))
                    # Deduct stock
                    c.execute('UPDATE products SET stock=stock-? WHERE id=?', (int(qty), pid))
                    c.execute('INSERT INTO stock_log (product_id,qty_change,reason) VALUES (?,?,?)',
                              (pid, -int(qty), f'ออเดอร์ {order_no}'))

        flash(f'สร้างออเดอร์ {order_no} สำเร็จ ✦')
        return redirect(url_for('order_detail', oid=oid))

    with get_db() as c:
        products  = c.execute('SELECT * FROM products WHERE active=1 ORDER BY name').fetchall()
        customers = c.execute('SELECT * FROM customers ORDER BY name').fetchall()
    return render_template('order_new.html', products=products, customers=customers)

@app.route('/orders/<int:oid>')
@login_required
def order_detail(oid):
    with get_db() as c:
        order = c.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
        if not order:
            return redirect(url_for('orders'))
        items = c.execute('SELECT * FROM order_items WHERE order_id=?', (oid,)).fetchall()
        cust  = c.execute('SELECT * FROM customers WHERE id=?', (order['customer_id'],)).fetchone() if order['customer_id'] else None
    return render_template('order_detail.html', order=order, items=items, cust=cust)

@app.route('/orders/<int:oid>/status', methods=['POST'])
@login_required
def order_status(oid):
    new_status = request.form.get('status')
    tracking   = request.form.get('tracking', '')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as c:
        c.execute('UPDATE orders SET status=?, tracking=?, updated_at=? WHERE id=?',
                  (new_status, tracking, now, oid))
    flash('อัปเดตสถานะแล้ว ✦')
    return redirect(url_for('order_detail', oid=oid))

# ── CUSTOMERS ────────────────────────────────────────────────────────────────
@app.route('/customers')
@login_required
def customers():
    search   = request.args.get('q', '')
    filter_t = request.args.get('type', 'all')
    with get_db() as c:
        custs = c.execute('''
            SELECT c.*,
                COUNT(o.id) as order_count,
                COALESCE(SUM(o.total),0) as total_spend,
                MAX(o.created_at) as last_order
            FROM customers c
            LEFT JOIN orders o ON o.customer_id=c.id AND o.status!='cancelled'
            WHERE (c.name LIKE ? OR c.social LIKE ? OR c.phone LIKE ?)
            GROUP BY c.id
            ORDER BY last_order DESC NULLS LAST
        ''', (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    return render_template('customers.html', customers=custs,
                           search=search, filter_t=filter_t)

@app.route('/customers/<int:cid>')
@login_required
def customer_detail(cid):
    with get_db() as c:
        cust   = c.execute('SELECT * FROM customers WHERE id=?', (cid,)).fetchone()
        orders = c.execute('''
            SELECT * FROM orders WHERE customer_id=? ORDER BY created_at DESC
        ''', (cid,)).fetchall()
        stats  = c.execute('''
            SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as total
            FROM orders WHERE customer_id=? AND status!='cancelled'
        ''', (cid,)).fetchone()
    return render_template('customer_detail.html', cust=cust, orders=orders, stats=stats)

# ── INVENTORY ────────────────────────────────────────────────────────────────
@app.route('/inventory')
@login_required
def inventory():
    with get_db() as c:
        products = c.execute('SELECT * FROM products WHERE active=1 ORDER BY name').fetchall()
        logs     = c.execute('''
            SELECT sl.*, p.name as product_name
            FROM stock_log sl JOIN products p ON p.id=sl.product_id
            ORDER BY sl.created_at DESC LIMIT 20
        ''').fetchall()
    return render_template('inventory.html', products=products, logs=logs)

@app.route('/inventory/add', methods=['POST'])
@login_required
def inventory_add():
    name  = request.form.get('name', '').strip()
    sku   = request.form.get('sku', '').strip()
    price = float(request.form.get('price', 0) or 0)
    cost  = float(request.form.get('cost', 0) or 0)
    stock = int(request.form.get('stock', 0) or 0)
    alert = int(request.form.get('low_alert', 10) or 10)
    with get_db() as c:
        c.execute('INSERT INTO products (name,sku,price,cost,stock,low_alert) VALUES (?,?,?,?,?,?)',
                  (name, sku, price, cost, stock, alert))
    flash(f'เพิ่มสินค้า "{name}" แล้ว ✦')
    return redirect(url_for('inventory'))

@app.route('/inventory/<int:pid>/adjust', methods=['POST'])
@login_required
def stock_adjust(pid):
    qty    = int(request.form.get('qty', 0) or 0)
    reason = request.form.get('reason', 'ปรับสต็อก')
    with get_db() as c:
        c.execute('UPDATE products SET stock=stock+? WHERE id=?', (qty, pid))
        c.execute('INSERT INTO stock_log (product_id,qty_change,reason) VALUES (?,?,?)',
                  (pid, qty, reason))
    flash('ปรับสต็อกแล้ว ✦')
    return redirect(url_for('inventory'))

# ── LEADS ────────────────────────────────────────────────────────────────────
@app.route('/leads')
@login_required
def leads():
    with get_db() as c:
        lead_list = c.execute('SELECT * FROM leads ORDER BY created_at DESC').fetchall()
    return render_template('leads.html', leads=lead_list)

@app.route('/leads/add', methods=['POST'])
@login_required
def lead_add():
    with get_db() as c:
        c.execute('INSERT INTO leads (name,source,status,budget,notes) VALUES (?,?,?,?,?)',
                  (request.form['name'], request.form.get('source','Facebook'),
                   'new', float(request.form.get('budget',0) or 0),
                   request.form.get('notes','')))
    flash('เพิ่ม Lead แล้ว ✦')
    return redirect(url_for('leads'))

@app.route('/leads/<int:lid>/status', methods=['POST'])
@login_required
def lead_status(lid):
    with get_db() as c:
        c.execute('UPDATE leads SET status=? WHERE id=?', (request.form['status'], lid))
    return redirect(url_for('leads'))

# ── REPORTS ──────────────────────────────────────────────────────────────────
@app.route('/reports')
@login_required
def reports():
    period = request.args.get('period', 'month')
    with get_db() as c:
        if period == 'today':
            dt_filter = "DATE(created_at)=DATE('now')"
        elif period == 'week':
            dt_filter = "DATE(created_at)>=DATE('now','-7 days')"
        else:
            dt_filter = "strftime('%Y-%m',created_at)=strftime('%Y-%m','now')"

        revenue   = c.execute(f"SELECT COALESCE(SUM(total),0) FROM orders WHERE {dt_filter} AND status!='cancelled'").fetchone()[0]
        ord_count = c.execute(f"SELECT COUNT(*) FROM orders WHERE {dt_filter} AND status!='cancelled'").fetchone()[0]
        new_custs = c.execute(f"SELECT COUNT(*) FROM customers WHERE {dt_filter}").fetchone()[0]

        # Channel breakdown
        channels  = c.execute(f'''
            SELECT channel, COUNT(*) as cnt, COALESCE(SUM(total),0) as rev
            FROM orders WHERE {dt_filter} AND status!='cancelled'
            GROUP BY channel ORDER BY rev DESC
        ''').fetchall()

        # Top products
        top_prods = c.execute(f'''
            SELECT oi.product_name, SUM(oi.qty) as qty, SUM(oi.total) as rev
            FROM order_items oi JOIN orders o ON o.id=oi.order_id
            WHERE {dt_filter} AND o.status!='cancelled'
            GROUP BY oi.product_name ORDER BY rev DESC LIMIT 5
        ''').fetchall()

        # Daily revenue last 30 days
        daily = c.execute('''
            SELECT DATE(created_at) as day, COALESCE(SUM(total),0) as rev
            FROM orders WHERE DATE(created_at)>=DATE('now','-29 days') AND status!='cancelled'
            GROUP BY day ORDER BY day
        ''').fetchall()

        campaigns = c.execute('SELECT * FROM campaigns ORDER BY created_at DESC').fetchall()

    return render_template('reports.html',
        revenue=revenue, ord_count=ord_count, new_custs=new_custs,
        channels=channels, top_prods=top_prods, daily=daily,
        campaigns=campaigns, period=period)

# ── API (AJAX) ───────────────────────────────────────────────────────────────
@app.route('/api/customers')
@login_required
def api_customers():
    q = request.args.get('q', '')
    with get_db() as c:
        rows = c.execute(
            'SELECT id,name,social,phone FROM customers WHERE name LIKE ? OR social LIKE ? LIMIT 10',
            (f'%{q}%', f'%{q}%')
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/products')
@login_required
def api_products():
    with get_db() as c:
        rows = c.execute('SELECT id,name,price,stock FROM products WHERE active=1').fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
