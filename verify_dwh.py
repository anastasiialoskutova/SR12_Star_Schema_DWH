import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON;")

# 1. Виконання DDL із файлу schema.sql
with open("schema.sql", "r", encoding="utf-8") as f:
    ddl_script = f.read()
conn.executescript(ddl_script)
print("[OK] DDL-схему успішно розгорнуто в базі даних.\n")

# 2. Наповнення вимірів тестовими даними
conn.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
    (20261015, '2026-10-15', 'Thursday', 0, 10, 'October', 4, 2026),
    (20261110, '2026-11-10', 'Tuesday',  0, 11, 'November', 4, 2026),
    (20261121, '2026-11-21', 'Saturday', 1, 11, 'November', 4, 2026),
])

# Демонстрація SCD Type 2: клієнт CUST_01 перейшов із Basic у Gold у листопаді 2026
conn.executemany("INSERT INTO dim_customer (customer_id, full_name, city, region, loyalty_tier, valid_from, valid_to, is_current) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
    ('CUST_01', 'Олена Коваль', 'Львів', 'Західний', 'Basic', '2026-01-01', '2026-10-31', 0),
    ('CUST_01', 'Олена Коваль', 'Львів', 'Західний', 'Gold',  '2026-11-01', '9999-12-31', 1),
    ('CUST_02', 'Максим Бондар', 'Київ', 'Центральний', 'Silver', '2026-03-15', '9999-12-31', 1),
])

conn.executemany("INSERT INTO dim_product (product_id, product_name, brand, subcategory, category, unit_cost) VALUES (?, ?, ?, ?, ?, ?)", [
    ('PROD_101', 'Навушники AirPulse Pro', 'SoundTech', 'Аудіо', 'Електроніка', 3000.00),
    ('PROD_102', 'Кавоварка Espresso Mini', 'HomeBrew', 'Кавова техніка', 'Побутова техніка', 5500.00),
    ('PROD_103', 'Рюкзак Urban 25L', 'PeakGear', 'Міські рюкзаки', 'Аксесуари', 900.00),
])

conn.executemany("INSERT INTO dim_channel (channel_code, platform_name, channel_type) VALUES (?, ?, ?)", [
    ('CH_IOS', 'iOS App', 'Mobile'),
    ('CH_WEB', 'Web Desktop', 'Web'),
])

# 3. Наповнення таблиці фактів (зерно = 1 позиція в замовленні)
conn.executemany("""
    INSERT INTO fact_sales (order_id, date_key, customer_sk, product_sk, channel_sk, quantity, gross_amount, discount_amount, net_revenue, profit_amount, margin_pct)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [
    ('ORD-1001', 20261015, 1, 1, 1, 1, 4500.00, 0.00,   4500.00, 1500.00, 33.33), # Олена ще у статусі Basic (sk=1)
    ('ORD-1001', 20261015, 1, 3, 1, 2, 3000.00, 300.00, 2700.00, 900.00,  33.33),
    ('ORD-1002', 20261110, 2, 2, 2, 1, 8000.00, 800.00, 7200.00, 1700.00, 23.61), # Олена вже у статусі Gold (sk=2)
    ('ORD-1003', 20261121, 3, 1, 1, 2, 9000.00, 450.00, 8550.00, 2550.00, 29.82), # Максим у вихідний день
])

QUERIES = [
    ("Q1. Яка чиста виручка, прибуток та реальна маржинальність за категоріями товарів?", """
        SELECT p.category,
               SUM(f.quantity) AS total_units,
               SUM(f.net_revenue) AS total_revenue,
               SUM(f.profit_amount) AS total_profit,
               ROUND(SUM(f.profit_amount) / SUM(f.net_revenue) * 100, 2) AS real_margin_pct
        FROM fact_sales f
        JOIN dim_product p ON f.product_sk = p.product_sk
        GROUP BY p.category
        ORDER BY total_revenue DESC;
    """),
    ("Q2. Як розподіляється виручка за історичними сегментами лояльності (SCD Type 2)?", """
        SELECT c.loyalty_tier,
               COUNT(DISTINCT f.order_id) AS orders_count,
               SUM(f.net_revenue) AS net_revenue
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_sk = c.customer_sk
        GROUP BY c.loyalty_tier
        ORDER BY net_revenue DESC;
    """),
    ("Q3. Яка динаміка продажів у розрізі місяців та типів каналів (Mobile vs Web)?", """
        SELECT d.year_num, d.month_name, ch.channel_type,
               SUM(f.net_revenue) AS revenue,
               SUM(f.discount_amount) AS discounts
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_channel ch ON f.channel_sk = ch.channel_sk
        GROUP BY d.year_num, d.month_name, ch.channel_type;
    """),
    ("Q4. Яка частка виручки припадає на вихідні дні порівняно з буднями?", """
        SELECT CASE WHEN d.is_weekend = 1 THEN 'Вихідні' ELSE 'Будні' END AS day_type,
               COUNT(DISTINCT f.order_id) AS orders,
               SUM(f.net_revenue) AS revenue
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.is_weekend;
    """),
    ("Q5. Який середній чек замовлення (AOV) у розрізі регіонів клієнтів?", """
        SELECT c.region,
               COUNT(DISTINCT f.order_id) AS unique_orders,
               ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_sk = c.customer_sk
        GROUP BY c.region;
    """)
]

for title, sql in QUERIES:
    print(f"=== {title} ===")
    cur = conn.execute(sql)
    cols = [desc[0] for desc in cur.description]
    print(" | ".join(cols))
    for row in cur.fetchall():
        print(" | ".join(str(val) for val in row))
    print()

conn.close()
