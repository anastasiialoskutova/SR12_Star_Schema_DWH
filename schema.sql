-- ==========================================================
-- Зіркова схема DWH для аналітики продажів (E-Commerce)
-- Зерно факту: 1 рядок (позиція) у замовленні клієнта
-- ==========================================================

-- 1. Вимір часу (Dim_Date) — ієрархія: Рік -> Квартал -> Місяць -> День
CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY, -- сурогатний ключ формату YYYYMMDD
    full_date       DATE NOT NULL,
    day_of_week     VARCHAR(15) NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    month_num       INTEGER NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    quarter_num     INTEGER NOT NULL,
    year_num        INTEGER NOT NULL
);

-- 2. Вимір клієнтів (Dim_Customer) — SCD Type 2 для сегмента (tier) та міста
CREATE TABLE dim_customer (
    customer_sk     INTEGER PRIMARY KEY AUTOINCREMENT, -- сурогатний ключ версії
    customer_id     VARCHAR(20) NOT NULL,              -- натуральний бізнес-ключ
    full_name       VARCHAR(100) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    region          VARCHAR(50) NOT NULL,
    loyalty_tier    VARCHAR(20) NOT NULL,              -- Basic / Silver / Gold (SCD2)
    valid_from      DATE NOT NULL,
    valid_to        DATE NOT NULL,
    is_current      BOOLEAN NOT NULL
);

-- 3. Вимір товарів (Dim_Product) — ієрархія: Категорія -> Підкатегорія -> Бренд -> Товар (SCD Type 1)
CREATE TABLE dim_product (
    product_sk      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      VARCHAR(20) NOT NULL UNIQUE,
    product_name    VARCHAR(120) NOT NULL,
    brand           VARCHAR(50) NOT NULL,
    subcategory     VARCHAR(50) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    unit_cost       DECIMAL(10, 2) NOT NULL
);

-- 4. Вимір каналів продажу (Dim_Channel) — ієрархія: Тип каналу -> Платформа
CREATE TABLE dim_channel (
    channel_sk      INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_code    VARCHAR(20) NOT NULL UNIQUE,
    platform_name   VARCHAR(50) NOT NULL, -- iOS App, Android App, Web Desktop, Web Mobile
    channel_type    VARCHAR(30) NOT NULL  -- Mobile vs Web
);

-- 5. Таблиця фактів (Fact_Sales)
CREATE TABLE fact_sales (
    sales_fact_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        VARCHAR(30) NOT NULL, -- дегенерований вимір (Degenerate Dimension)
    date_key        INTEGER NOT NULL,
    customer_sk     INTEGER NOT NULL,
    product_sk      INTEGER NOT NULL,
    channel_sk      INTEGER NOT NULL,
    -- Міри (Measures):
    quantity        INTEGER NOT NULL,        -- Адитивна (Additive)
    gross_amount    DECIMAL(12, 2) NOT NULL, -- Адитивна (Additive)
    discount_amount DECIMAL(12, 2) NOT NULL, -- Адитивна (Additive)
    net_revenue     DECIMAL(12, 2) NOT NULL, -- Адитивна (Additive)
    profit_amount   DECIMAL(12, 2) NOT NULL, -- Адитивна (Additive)
    margin_pct      DECIMAL(5, 2) NOT NULL,  -- Неадитивна (Non-additive: відсоток маржі)
    FOREIGN KEY (date_key)    REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk),
    FOREIGN KEY (product_sk)  REFERENCES dim_product(product_sk),
    FOREIGN KEY (channel_sk)  REFERENCES dim_channel(channel_sk)
);
