-- MySQL 8.0 schema for fashion-shop
-- Engine: InnoDB, Charset: utf8mb4
-- Run order-safe: drops first, then creates

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Optional: create and use dedicated database
CREATE DATABASE IF NOT EXISTS fashion_shop
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE fashion_shop;

-- =============================
-- Drop existing tables (if any)
-- =============================
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS inventory_locks;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS carts;
DROP TABLE IF EXISTS banners;
DROP TABLE IF EXISTS product_skus;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================
-- Users and Admins
-- =============================
CREATE TABLE users (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email           VARCHAR(255) NULL,
  phone           VARCHAR(20) NULL,
  password_hash   VARCHAR(255) NOT NULL,
  nickname        VARCHAR(64) NULL,
  avatar          VARCHAR(512) NULL,
  status          ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  last_login_at   DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email (email),
  UNIQUE KEY uk_users_phone (phone),
  KEY idx_users_status (status),
  KEY idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='前台用户';

CREATE TABLE admins (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username        VARCHAR(64) NOT NULL,
  password_hash   VARCHAR(255) NOT NULL,
  role            ENUM('SUPER','OPERATOR') NOT NULL DEFAULT 'OPERATOR',
  status          ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
  last_login_at   DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_admins_username (username),
  KEY idx_admins_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='后台管理员';

CREATE TABLE addresses (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id         BIGINT UNSIGNED NOT NULL,
  contact_name    VARCHAR(64) NOT NULL,
  contact_phone   VARCHAR(20) NOT NULL,
  province        VARCHAR(64) NOT NULL,
  city            VARCHAR(64) NOT NULL,
  district        VARCHAR(64) NOT NULL,
  detail          VARCHAR(255) NOT NULL,
  is_default      TINYINT(1) NOT NULL DEFAULT 0,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_addresses_user (user_id),
  CONSTRAINT fk_addresses_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户收货地址';

-- =============================
-- Categories and Products
-- =============================
CREATE TABLE categories (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  parent_id       BIGINT UNSIGNED NULL,
  name            VARCHAR(128) NOT NULL,
  level           TINYINT UNSIGNED NOT NULL DEFAULT 1,
  sort_order      INT NOT NULL DEFAULT 0,
  is_visible      TINYINT(1) NOT NULL DEFAULT 1,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_categories_parent_name (parent_id, name),
  KEY idx_categories_visible (is_visible),
  CONSTRAINT fk_categories_parent
    FOREIGN KEY (parent_id) REFERENCES categories(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品分类';

CREATE TABLE products (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id     BIGINT UNSIGNED NULL,
  title           VARCHAR(255) NOT NULL,
  subtitle        VARCHAR(255) NULL,
  description     TEXT NULL,
  cover_image     VARCHAR(512) NULL,
  status          ENUM('DRAFT','ON_SALE','OFF_SALE') NOT NULL DEFAULT 'DRAFT',
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_products_category (category_id),
  KEY idx_products_status (status),
  CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品SPU';

CREATE TABLE product_skus (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id      BIGINT UNSIGNED NOT NULL,
  sku_code        VARCHAR(64) NOT NULL,
  color           VARCHAR(64) NULL,
  size            VARCHAR(64) NULL,
  price           DECIMAL(10,2) NOT NULL,
  stock           INT NOT NULL DEFAULT 0,
  image           VARCHAR(512) NULL,
  bar_code        VARCHAR(64) NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_skus_code (sku_code),
  UNIQUE KEY uk_skus_product_variant (product_id, color, size),
  KEY idx_skus_product (product_id),
  KEY idx_skus_active (is_active),
  CONSTRAINT chk_skus_price CHECK (price >= 0),
  CONSTRAINT chk_skus_stock CHECK (stock >= 0),
  CONSTRAINT fk_skus_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品SKU';

CREATE TABLE banners (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  image_url       VARCHAR(512) NOT NULL,
  link_url        VARCHAR(512) NULL,
  sort_order      INT NOT NULL DEFAULT 0,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_banners_active (is_active),
  KEY idx_banners_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='首页Banner';

-- =============================
-- Cart
-- =============================
CREATE TABLE carts (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id         BIGINT UNSIGNED NOT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_carts_user (user_id),
  CONSTRAINT fk_carts_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='购物车';

CREATE TABLE cart_items (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  cart_id         BIGINT UNSIGNED NOT NULL,
  sku_id          BIGINT UNSIGNED NOT NULL,
  quantity        INT NOT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cartitem_unique (cart_id, sku_id),
  KEY idx_cartitems_cart (cart_id),
  KEY idx_cartitems_sku (sku_id),
  CONSTRAINT chk_cartitem_qty CHECK (quantity > 0),
  CONSTRAINT fk_cartitems_cart
    FOREIGN KEY (cart_id) REFERENCES carts(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_cartitems_sku
    FOREIGN KEY (sku_id) REFERENCES product_skus(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='购物车明细';

-- =============================
-- Orders
-- =============================
CREATE TABLE orders (
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_no          VARCHAR(64) NOT NULL,
  user_id           BIGINT UNSIGNED NOT NULL,
  -- address snapshot
  receiver_name     VARCHAR(64) NOT NULL,
  receiver_phone    VARCHAR(20) NOT NULL,
  province          VARCHAR(64) NOT NULL,
  city              VARCHAR(64) NOT NULL,
  district          VARCHAR(64) NOT NULL,
  address_detail    VARCHAR(255) NOT NULL,
  remark            VARCHAR(255) NULL,
  status            ENUM('UNPAID','PAID','SHIPPING','SHIPPED','COMPLETED','CANCELED') NOT NULL DEFAULT 'UNPAID',
  amount_total      DECIMAL(10,2) NOT NULL,
  amount_payable    DECIMAL(10,2) NOT NULL,
  pay_channel       ENUM('NONE','ALIPAY') NOT NULL DEFAULT 'NONE',
  paid_at           DATETIME NULL,
  canceled_at       DATETIME NULL,
  completed_at      DATETIME NULL,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_orders_no (order_no),
  KEY idx_orders_user (user_id),
  KEY idx_orders_status (status),
  KEY idx_orders_created (created_at),
  CONSTRAINT chk_orders_amounts CHECK (amount_total >= 0 AND amount_payable >= 0),
  CONSTRAINT fk_orders_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='订单主表';

CREATE TABLE order_items (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id        BIGINT UNSIGNED NOT NULL,
  product_id      BIGINT UNSIGNED NULL,
  sku_id          BIGINT UNSIGNED NULL,
  title           VARCHAR(255) NOT NULL,
  sku_attrs       JSON NULL,
  unit_price      DECIMAL(10,2) NOT NULL,
  quantity        INT NOT NULL,
  total_price     DECIMAL(10,2) NOT NULL,
  cover_image     VARCHAR(512) NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_orderitems_order (order_id),
  KEY idx_orderitems_sku (sku_id),
  CONSTRAINT chk_orderitem_qty CHECK (quantity > 0),
  CONSTRAINT chk_orderitem_prices CHECK (unit_price >= 0 AND total_price >= 0),
  CONSTRAINT fk_orderitems_order
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_orderitems_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT fk_orderitems_sku
    FOREIGN KEY (sku_id) REFERENCES product_skus(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='订单明细';

CREATE TABLE inventory_locks (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id        BIGINT UNSIGNED NOT NULL,
  sku_id          BIGINT UNSIGNED NOT NULL,
  quantity        INT NOT NULL,
  status          ENUM('LOCKED','RELEASED','CONSUMED') NOT NULL DEFAULT 'LOCKED',
  expires_at      DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_invlock_order_sku (order_id, sku_id),
  KEY idx_invlock_sku_status (sku_id, status),
  CONSTRAINT chk_invlock_qty CHECK (quantity > 0),
  CONSTRAINT fk_invlock_order
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_invlock_sku
    FOREIGN KEY (sku_id) REFERENCES product_skus(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='库存预占';

-- =============================
-- Payments
-- =============================
CREATE TABLE payments (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id        BIGINT UNSIGNED NOT NULL,
  channel         ENUM('ALIPAY') NOT NULL,
  out_trade_no    VARCHAR(64) NOT NULL,     -- 商户支付单号（建议等于 order_no）
  trade_no        VARCHAR(128) NULL,        -- 支付宝交易号
  amount          DECIMAL(10,2) NOT NULL,
  status          ENUM('INIT','SUCCESS','FAILED','CLOSED') NOT NULL DEFAULT 'INIT',
  request_params  JSON NULL,
  notify_payload  JSON NULL,
  paid_at         DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_payments_out_trade_no (out_trade_no),
  KEY idx_payments_order (order_id),
  KEY idx_payments_status (status),
  CONSTRAINT chk_payments_amount CHECK (amount >= 0),
  CONSTRAINT fk_payments_order
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='支付记录';

-- =============================
-- Shipments
-- =============================
CREATE TABLE shipments (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id        BIGINT UNSIGNED NOT NULL,
  company         VARCHAR(64) NOT NULL,
  tracking_no     VARCHAR(64) NOT NULL,
  status          ENUM('CREATED','SHIPPED','DELIVERED') NOT NULL DEFAULT 'CREATED',
  shipped_at      DATETIME NULL,
  delivered_at    DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_shipments_tracking (tracking_no),
  KEY idx_shipments_order (order_id),
  KEY idx_shipments_status (status),
  CONSTRAINT fk_shipments_order
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='发货记录';

-- =============================
-- Helpful seed (optional)
-- =============================
-- INSERT INTO admins (username, password_hash, role) VALUES ('admin', '<bcrypt_hash_here>', 'SUPER');

-- Done