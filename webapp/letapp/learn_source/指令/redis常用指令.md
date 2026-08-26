# redis常用指令

## **1. 服务管理**

### **启动/关闭 Redis**

``` bash
# 启动 Redis 服务端（默认端口 6379）
redis-server
redis-server --port 6380           # 指定端口

# 启动 Redis 客户端
redis-cli
redis-cli -h 127.0.0.1 -p 6379     # 连接远程 Redis

# 关闭 Redis
redis-cli shutdown                 # 安全关闭
redis-cli shutdown nosave          # 强制关闭（不保存数据）
```

## **2. Key 操作**

### **基本 Key 操作**

``` bash
SET key value                      # 设置键值
GET key                            # 获取键值
DEL key                            # 删除键
EXISTS key                         # 检查键是否存在
EXPIRE key 10                      # 设置键 10 秒后过期
TTL key                            # 查看键剩余生存时间（秒）
KEYS pattern                       # 查找键（谨慎使用，可能阻塞）
SCAN cursor [MATCH pattern] [COUNT n] # 安全遍历键（代替 KEYS）
```

### **批量操作**

``` bash
MSET key1 val1 key2 val2           # 批量设置键值
MGET key1 key2                     # 批量获取键值
UNLINK key1 key2                   # 异步删除（高并发推荐）
```

## **3. 数据类型操作**

### **String（字符串）**

``` bash
INCR key                           # 值 +1（限数字）
DECR key                           # 值 -1
APPEND key "value"                 # 追加字符串
STRLEN key                         # 获取字符串长度
```

### **List（列表）**

``` bash
LPUSH list value                   # 左端插入
RPUSH list value                   # 右端插入
LPOP list                          # 左端弹出
RPOP list                          # 右端弹出
LLEN list                          # 获取列表长度
LRANGE list 0 -1                   # 获取全部元素
```

### **Hash（哈希表）**

```bash
<BASH>
HSET user name John age 30         # 设置字段
HGET user name                     # 获取字段
HGETALL user                       # 获取所有字段
HDEL user age                      # 删除字段
```

### **Set（集合）**

```bash
<BASH>
SADD tags redis db                 # 添加元素
SMEMBERS tags                      # 获取所有元素
SISMEMBER tags redis               # 检查元素是否存在
SREM tags db                       # 删除元素
```

### **Sorted Set（有序集合）**

```bash
<BASH>
ZADD rankings 100 "Alice"          # 添加带分数的成员
ZRANGE rankings 0 -1               # 按排名获取成员
ZREVRANGE rankings 0 -1            # 按分数从高到低获取
ZSCORE rankings "Alice"            # 获取成员分数
```

------

## **4. 服务器管理与监控**

### **查看 Redis 信息**

```bash
<BASH>
INFO                               # 查看全部信息
INFO memory                        # 查看内存使用
INFO clients                       # 查看客户端连接
INFO replication                   # 查看主从复制状态
```

### **配置管理**

```bash
<BASH>
CONFIG GET *                       # 查看所有配置（慎用）
CONFIG GET maxmemory               # 查看指定配置
CONFIG SET maxmemory 1GB           # 动态修改配置
CONFIG REWRITE                     # 保存配置到 redis.conf
```

### **性能测试**

```bash
<BASH>
redis-benchmark -n 100000          # 10 万次请求测试
redis-benchmark -c 50 -n 100000    # 50 并发测试
```

### **持久化控制**

```bash
<BASH>
SAVE                               # 同步保存数据到 RDB
BGSAVE                             # 后台保存数据
LASTSAVE                           # 最后一次保存时间戳
```

------

## **5. 安全与连接管理**

```bash
<BASH>
AUTH password                      # 认证密码（若启用）
CLIENT LIST                        # 查看所有客户端
CLIENT KILL ip:port                # 踢出指定客户端
PING                               # 测试服务器是否存活
SELECT 1                           # 切换到数据库 1（默认 16 个）
```

------

## **6. 集群与分布式**

### **主从复制**

```bash
<BASH>
REPLICAOF host port                # 设置为从节点
INFO replication                   # 查看复制状态
```

### **Redis Cluster**

```bash
<BASH>
CLUSTER INFO                       # 查看集群状态
CLUSTER NODES                      # 列出集群节点
CLUSTER MEET ip port               # 手动添加节点
```

------

## **常用命令速查表**

| **类别**     | **命令示例**               | **作用**          |
| :----------- | :------------------------- | :---------------- |
| **服务管理** | `redis-server` `redis-cli` | 启动服务/客户端   |
| **Key 操作** | `SET` `GET` `DEL` `TTL`    | 增删改查键值      |
| **List**     | `LPUSH` `RPOP` `LRANGE`    | 列表操作          |
| **Hash**     | `HSET` `HGET` `HGETALL`    | 哈希表操作        |
| **Set**      | `SADD` `SMEMBERS` `SREM`   | 集合操作          |
| **监控**     | `INFO` `CLIENT LIST`       | 查看状态和连接    |
| **持久化**   | `SAVE` `BGSAVE`            | 手动触发 RDB 保存 |