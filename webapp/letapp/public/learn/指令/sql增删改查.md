# sql增删改查

## 创建表（CREATE TABLE）

``` sql	
-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

```

## 增（INSERT）

``` sql
-- 插入单条用户数据
INSERT INTO users (username, email, password) 
VALUES ('john_doe', 'john@example.com', 'securepassword123');

-- 插入多条用户数据
INSERT INTO users (username, email, password) VALUES 
('jane_smith', 'jane@example.com', 'janespassword456'),
('mike_jones', 'mike@example.com', 'mikepassword789');

-- 插入订单数据
INSERT INTO orders (user_id, total_amount) 
VALUES (1, 99.99);

```

## 删（DELETE）

``` sql
-- 删除特定条件的用户（删除ID为3的用户）
DELETE FROM users WHERE id = 3;

-- 删除所有状态为'cancelled'的订单
DELETE FROM orders WHERE status = 'cancelled';

-- 删除表中的所有数据（谨慎使用！）
-- DELETE FROM users;

```

## 改（UPDATE）

``` sql
-- 更新单个用户的电子邮件
UPDATE users SET email = 'john.new@example.com' WHERE id = 1;

-- 更新多个字段
UPDATE users 
SET username = 'john_doe_updated', password = 'newsecurepassword'
WHERE id = 1;

-- 批量更新订单状态
UPDATE orders 
SET status = 'completed', updated_at = CURRENT_TIMESTAMP
WHERE status = 'processing' AND order_date < '2023-01-01';

```

## 查（SELECT）

``` sql
-- 查询所有用户
SELECT * FROM users;

-- 查询特定列
SELECT username, email FROM users;

-- 带条件的查询
SELECT * FROM users WHERE username = 'john_doe';

-- 模糊查询
SELECT * FROM users WHERE username LIKE 'j%';

-- 排序
SELECT * FROM users ORDER BY created_at DESC;

-- 分页查询 (MySQL语法)
SELECT * FROM users LIMIT 10 OFFSET 20;

```

