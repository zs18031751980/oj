# MySQL 常考语句分类整理

> 来源: https://notes.kamacoder.com/base/sql.html

# MySQL 常考语句分类整理

## 一、数据查询（SELECT）

| 类型  示例
| 基础查询  `SELECT * FROM users;`
| 指定列  `SELECT id, name FROM users;`
| 条件查询  `SELECT * FROM users WHERE age > 25;`
| 排序  `SELECT * FROM users ORDER BY age DESC;`
| 去重  `SELECT DISTINCT city FROM users;`
| 分页  `SELECT * FROM users LIMIT 10 OFFSET 20;`
| 别名  `SELECT name AS username FROM users;`
| 模糊匹配  `SELECT * FROM users WHERE name LIKE 'A%';`
| 范围查询  `SELECT * FROM users WHERE age BETWEEN 20 AND 30;`
| 多条件  `SELECT * FROM users WHERE age > 20 AND city = 'Beijing';`

## 二、多表操作（连接与子查询）

| 类型  示例
| 内连接  `SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id;`
| 左连接  `SELECT u.name, o.amount FROM users u LEFT JOIN orders o ON u.id = o.user_id;`
| 右连接  `SELECT u.name, o.amount FROM users u RIGHT JOIN orders o ON u.id = o.user_id;`
| 子查询（WHERE中）  `SELECT name FROM users WHERE id IN (SELECT user_id FROM orders);`
| 子查询（FROM中）  `SELECT t.user_id, COUNT(*) FROM (SELECT * FROM orders WHERE amount > 100) t GROUP BY t.user_id;`

## 三、聚合与分组

| 类型  示例
| 总数  `SELECT COUNT(*) FROM users;`
| 求和  `SELECT SUM(amount) FROM orders;`
| 平均值  `SELECT AVG(age) FROM users;`
| 最大/最小值  `SELECT MAX(age), MIN(age) FROM users;`
| 分组统计  `SELECT city, COUNT(*) FROM users GROUP BY city;`
| 分组条件  `SELECT city, COUNT(*) FROM users GROUP BY city HAVING COUNT(*) > 10;`

## 四、数据更新与写入

| 类型  示例
| 插入  `INSERT INTO users(name, age) VALUES('Alice', 30);`
| 批量插入  `INSERT INTO users(name, age) VALUES ('Bob', 25), ('Cathy', 22);`
| 插入或更新  `INSERT INTO users(id, name) VALUES (1, 'Tom') ON DUPLICATE KEY UPDATE name='Tom';`
| 更新数据  `UPDATE users SET age = 28 WHERE id = 1;`
| 删除数据  `DELETE FROM users WHERE age < 18;`

## 五、索引与性能优化相关

| 类型  示例
| 查看索引  `SHOW INDEX FROM users;`
| 创建索引  `CREATE INDEX idx_age ON users(age);`
| 删除索引  `DROP INDEX idx_age ON users;`
| 使用执行计划  `EXPLAIN SELECT * FROM users WHERE age > 30;`
| 查看慢查询日志  `SHOW VARIABLES LIKE 'slow_query_log%';`
| 强制使用索引  `SELECT * FROM users FORCE INDEX (idx_age) WHERE age > 25;`

## 六、事务与锁操作

| 类型  示例
| 开启事务  `START TRANSACTION;` 或 `BEGIN;`
| 提交事务  `COMMIT;`
| 回滚事务  `ROLLBACK;`
| 设置隔离级别  `SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;`
| 查看当前隔离级别  `SELECT @@tx_isolation;`
| 悲观锁  `SELECT * FROM users WHERE id = 1 FOR UPDATE;`
| 乐观锁  `UPDATE users SET age = 26, version = version + 1 WHERE id = 1 AND version = 2;`

## Bonus：面试高频场景题

| 问题  示例
| 查询每个用户的最后一笔订单  使用 `GROUP BY` + `MAX(order_time)` 或 `子查询 + JOIN`
| 查询重复数据  `SELECT name, COUNT(*) FROM users GROUP BY name HAVING COUNT(*) > 1;`
| 查询某字段为空  `SELECT * FROM users WHERE phone IS NULL;`
| 查询某天注册的用户  `SELECT * FROM users WHERE DATE(register_time) = '2024-01-01';`
| 分页优化  `SELECT * FROM users WHERE id > ? LIMIT 10;` 替代 OFFSET
