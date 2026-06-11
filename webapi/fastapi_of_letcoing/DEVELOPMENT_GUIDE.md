# LetCoding API 开发新手教程

本教程将指导新手如何在 LetCoding API 项目中进行服务开发，包括依赖注入、控制器编写、Redis缓存使用和路由注册等核心概念。

## 📚 目录

1. [项目架构概览](#项目架构概览)
2. [依赖注入详解](#依赖注入详解)
3. [服务开发](#服务开发)
4. [数据库服务使用](#数据库服务使用)
5. [Redis 缓存服务使用](#redis-缓存服务使用)
6. [认证和授权开发](#认证和授权开发)
7. [控制器编写](#控制器编写)
8. [路由注册](#路由注册)
9. [完整开发流程示例](#完整开发流程示例)
10. [常见问题和最佳实践](#常见问题和最佳实践)

## 🏗️ 项目架构概览

### 目录结构
```
fastapi_of_letcoing/
├── core/                    # 核心模块
│   ├── di_container.py      # 依赖注入容器
│   └── service_config.py    # 服务配置
├── interfaces/              # 服务接口定义
│   ├── __init__.py
│   └── service_interfaces.py # 抽象接口
├── models/                  # 数据模型定义
│   ├── __init__.py
│   ├── glot_models.py      # Glot API 数据模型
│   ├── auth_models.py      # 认证相关数据模型
│   └── db_models.py        # 数据库模型（Peewee ORM）
├── services/               # 业务服务层
│   ├── config_service.py   # 配置服务
│   ├── glot_service.py     # 代码执行服务
│   ├── logger_service.py   # 日志服务
│   ├── oidc_service.py     # OIDC 认证服务
│   ├── jwt_service.py      # JWT 认证服务
│   ├── redis_service.py    # Redis 缓存服务
│   ├── database_service.py # 数据库基础服务
│   ├── user_service.py     # 用户服务
│   ├── code_execution_service.py # 代码执行记录服务
│   └── api_service.py      # API 密钥服务
├── middleware/             # 中间件层
│   └── auth_middleware.py  # JWT 认证中间件
├── controllers/            # 控制器层
│   ├── __init__.py
│   ├── code_controller.py  # 代码执行控制器
│   └── auth_controller.py  # 认证控制器
├── main.py                 # 应用入口
└── requirements.txt        # 依赖管理
```

### 架构层次
```
请求 → 中间件 → 控制器 → 服务层 → 数据库/Redis/外部API
```

## 🔄 依赖注入详解

### 什么是依赖注入？
依赖注入（Dependency Injection, DI）是一种设计模式，它将对象的依赖关系从内部创建转移到外部注入，提高代码的可测试性和解耦性。

### 生命周期类型

#### 1. Singleton（单例）
- **特点**: 整个应用生命周期内只有一个实例
- **适用场景**: 配置服务、日志服务等无状态服务
- **注册方式**:
```python
container.register_singleton(IConfigService, ConfigService)
# 或使用工厂方法
container.register_singleton(IConfigService, factory=lambda: ConfigService(app_config))
```

#### 2. Transient（瞬态）
- **特点**: 每次请求都创建新实例
- **适用场景**: 需要状态隔离的服务
- **注册方式**:
```python
container.register_transient(IMyService, MyService)
```

#### 3. Scoped（作用域）
- **特点**: 在单个请求周期内保持单例
- **适用场景**: Web应用中的请求相关服务
- **注册方式**:
```python
container.register_scoped(ICodeExecutionService, GlotService)
```

### 如何使用依赖注入

#### 方法1：构造函数注入（推荐）
```python
from interfaces.service_interfaces import IConfigService, ILoggerService
from core.di_container import Injectable

class MyService(Injectable):
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config = config_service
        self._logger = logger_service
    
    def do_something(self):
        api_token = self._config.get_api_token()
        self._logger.info(f"使用token: {api_token[:8]}...")
```

#### 方法2：运行时注入
```python
from core.di_container import inject
from interfaces.service_interfaces import ICodeExecutionService

def my_function():
    code_service = inject(ICodeExecutionService)
    # 使用服务...
```

## 🛠️ 服务开发

### 步骤1：定义服务接口

在 `interfaces/service_interfaces.py` 中添加新的服务接口：

```python
class IMyService(ABC):
    """我的服务接口"""
    
    @abstractmethod
    def process_data(self, data: str) -> str:
        """处理数据"""
        pass
    
    @abstractmethod
    def get_status(self) -> bool:
        """获取服务状态"""
        pass
```

### 步骤2：实现服务类

在 `services/` 目录下创建新文件：

```python
# services/my_service.py
from typing import Optional
from interfaces.service_interfaces import IMyService, IConfigService, ILoggerService
from core.di_container import Injectable

class MyService(IMyService, Injectable):
    """我的服务实现"""
    
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config_service = config_service
        self._logger_service = logger_service
    
    def process_data(self, data: str) -> str:
        """处理数据"""
        self._logger_service.info(f"开始处理数据: {data}")
        
        # 业务逻辑
        processed_data = data.upper()
        
        self._logger_service.info(f"数据处理完成: {processed_data}")
        return processed_data
    
    def get_status(self) -> bool:
        """获取服务状态"""
        try:
            # 检查配置
            token = self._config_service.get_api_token()
            return bool(token)
        except Exception as ex:
            self._logger_service.error("获取服务状态失败", ex)
            return False
```

### 步骤3：注册服务

在 `core/service_config.py` 中注册新服务：

```python
from services.my_service import MyService
from interfaces.service_interfaces import IMyService

def service_configurator(container):
    # ... 其他服务注册 ...
    
    # 注册我的服务
    container.register_singleton(IMyService, MyService)
```

### 服务开发最佳实践

1. **接口优先**: 先定义接口，再实现具体类
2. **单一职责**: 每个服务只负责一个具体功能
3. **依赖最小化**: 只注入真正需要的依赖
4. **数据持久化**: 合理使用数据库服务存储业务数据
5. **缓存策略**: 合理使用 Redis 缓存提高性能
6. **异常处理**: 在服务层统一处理异常
7. **日志记录**: 重要操作都要记录日志
8. **连接管理**: 数据库、Redis 等外部服务的连接状态管理

#### 缓存服务最佳实践

1. **键命名规范**: 使用有意义的键名和命名空间
   ```python
   # 好的命名
   user_cache_key = f"user:profile:{user_id}"
   rate_limit_key = f"rate_limit:api:{user_id}:{endpoint}"
   
   # 避免的命名
   key = "data123"
   ```

2. **TTL 设置**: 根据数据特性设置合理的过期时间
   ```python
   # 用户会话信息：短时间过期
   redis_service.set(f"session:{session_id}", session_data, ttl=1800)  # 30分钟
   
   # 用户基本信息：较长时间过期
   redis_service.set(f"user:profile:{user_id}", profile, ttl=3600)  # 1小时
   
   # 系统配置：长时间过期
   redis_service.set("system:config", config_data, ttl=86400)  # 24小时
   ```

3. **缓存穿透保护**: 使用空值缓存防止缓存穿透
   ```python
   def get_user_with_cache(user_id: str):
       cache_key = f"user:profile:{user_id}"
       
       # 尝试从缓存获取
       user = redis_service.get(cache_key)
       if user is not None:
           return user if user != "null" else None
       
       # 从数据库获取
       user = database_service.get_user(user_id)
       
       # 缓存结果（包括空值）
       cache_value = user.to_dict() if user else "null"
       redis_service.set(cache_key, cache_value, ttl=300)  # 空值缓存5分钟
       
       return user
   ```

4. **批量操作优化**: 使用 Redis 管道或批量操作
   ```python
   # 避免循环单个操作
   for user_id in user_ids:
       profile = redis_service.get(f"user:profile:{user_id}")
   
   # 推荐使用批量操作
   cache_keys = [f"user:profile:{uid}" for uid in user_ids]
   profiles = [redis_service.get(key) for key in cache_keys]
   ```

#### 认证服务最佳实践

1. **令牌安全**: 设置合理的令牌过期时间和强密钥
2. **刷新策略**: 实现令牌刷新机制，避免频繁重新登录
3. **权限控制**: 基于角色的访问控制
4. **会话管理**: 使用 Redis 管理用户会话状态

## 🗄️ 数据库服务使用

### 数据库服务概述

项目使用 PostgreSQL 数据库和 Peewee ORM 框架，采用模块化的数据库服务架构：

- **DatabaseService**: 基础数据库服务，提供通用 CRUD 操作和连接管理
- **UserService**: 用户相关数据库操作
- **CodeExecutionService**: 代码执行记录相关操作
- **APIService**: API 密钥管理相关操作

每个表都有专门的服务类继承自 DatabaseService，实现了更好的解耦和可维护性。数据库配置通过 ConfigService 统一管理，支持环境变量配置。

### 数据库模型设计

#### 基础模型类
```python
# models/db_models.py
from peewee import Model, CharField, TextField, DateTimeField, BooleanField, IntegerField, AutoField
from datetime import datetime

class BaseModel(Model):
    """基础模型类"""
    created_at = DateTimeField(default=datetime.now, verbose_name="创建时间")
    updated_at = DateTimeField(default=datetime.now, verbose_name="更新时间")
    
    class Meta:
        database = get_database()
    
    def save(self, force_insert=False, only=None):
        """保存时更新 updated_at 字段"""
        self.updated_at = datetime.now()
        return super().save(force_insert, only)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = {}
        for field_name in self._meta.fields.keys():
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[field_name] = value
        return data
```

#### 具体模型示例
```python
# 用户模型
class User(BaseModel):
    """用户模型"""
    id = AutoField(primary_key=True, verbose_name="用户ID")
    username = CharField(max_length=50, unique=True, null=False, verbose_name="用户名")
    email = CharField(max_length=100, unique=True, null=True, verbose_name="邮箱")
    password_hash = CharField(max_length=255, null=False, verbose_name="密码哈希")
    is_active = BooleanField(default=True, verbose_name="是否激活")
    last_login = DateTimeField(null=True, verbose_name="最后登录时间")
    
    class Meta:
        table_name = "users"
    
    def to_dict(self) -> dict:
        """转换为字典，排除敏感信息"""
        data = super().to_dict()
        data.pop("password_hash", None)
        return data
```

### 数据库服务架构

#### 基础数据库服务 (DatabaseService)
DatabaseService 提供通用的 CRUD 操作和数据库连接管理：

```python
# 基础 CRUD 操作
async def create(self, model_class: type, **kwargs) -> Dict[str, Any]
async def get_by_id(self, model_class: type, record_id: int) -> Optional[Dict[str, Any]]
async def update(self, model_class: type, record_id: int, **kwargs) -> bool
async def delete(self, model_class: type, record_id: int) -> bool
async def list_all(self, model_class: type, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]
async def count(self, model_class: type) -> int

# 数据库管理
def test_connection() -> bool
def get_database_info() -> Dict[str, Any]
def close()
```

#### 专门服务类继承 DatabaseService

##### UserService - 用户服务
```python
from services.user_service import UserService
from core.di_container import inject

# 使用用户服务
user_service = inject(UserService)

# 创建用户
user = await user_service.create_user("username", "password_hash", "email@example.com")

# 根据用户名获取用户
user = await user_service.get_user_by_username("username")

# 更新用户最后登录时间
await user_service.update_user_last_login(user_id)

# 获取用户列表
users = await user_service.list_users(limit=20, active_only=True)

# 搜索用户
results = await user_service.search_users("john")
```

#### 运行时注入方式
```python
from core.di_container import inject
from services.user_service import UserService
from services.code_execution_service import CodeExecutionService

async def analyze_user_activity(user_id: int):
    """分析用户活动"""
    user_service = inject(UserService)
    exec_service = inject(CodeExecutionService)
    
    # 获取用户信息
    user = await user_service.get_user_by_id(user_id)
    if not user:
        return {"error": "用户不存在"}
    
    # 获取执行统计信息
    stats = await exec_service.get_execution_statistics(user_id)
    
    return {
        "user": user,
        "statistics": stats,
        "total_executions": stats["total_executions"],
        "success_rate": stats["success_rate"],
        "favorite_languages": stats["language_distribution"]
    }
```

### 创建新的数据库服务

#### 步骤1：创建服务类
```python
# services/my_table_service.py
from datetime import datetime
from typing import List, Optional, Dict, Any

from services.database_service import DatabaseService
from models.db_models import MyModel
from core.di_container import Injectable

class MyTableService(DatabaseService, Injectable):
    """我的表服务类"""
    
    async def create_my_record(self, name: str, value: str) -> Dict[str, Any]:
        """创建记录"""
        try:
            record_data = await self.create(
                MyModel,
                name=name,
                value=value,
                is_active=True
            )
            return record_data
        except Exception as e:
            raise RuntimeError(f"创建记录时发生错误: {e}")
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取记录"""
        try:
            record = MyModel.get(MyModel.name == name)
            return record.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取记录时发生错误: {e}")
    
    async def list_active_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取活跃记录列表"""
        try:
            query = (MyModel
                    .select()
                    .where(MyModel.is_active == True)
                    .order_by(MyModel.created_at.desc())
                    .limit(limit))
            
            return [record.to_dict() for record in query]
        except Exception as e:
            raise RuntimeError(f"获取活跃记录时发生错误: {e}")
    
    async def deactivate_record(self, record_id: int) -> bool:
        """停用记录"""
        return await self.update(MyModel, record_id, is_active=False)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            total_records = MyModel.select().count()
            active_records = MyModel.select().where(MyModel.is_active == True).count()
            
            return {
                "total_records": total_records,
                "active_records": active_records,
                "inactive_records": total_records - active_records,
                "active_rate": active_records / total_records if total_records > 0 else 0
            }
        except Exception as e:
            raise RuntimeError(f"获取统计信息时发生错误: {e}")
```

#### 步骤2：注册服务
```python
# core/service_config.py
def create_my_table_service():
    config_service = container.resolve(IConfigService)
    return MyTableService(config_service)

def service_configurator(container):
    # ... 其他服务注册 ...
    container.register_singleton(MyTableService, factory=create_my_table_service)
```

#### 步骤3：使用服务
```python
from services.my_table_service import MyTableService

my_service = inject(MyTableService)

# 创建记录
record = await my_service.create_my_record("test", "value")

# 获取记录
record = await my_service.get_by_name("test")

# 获取统计信息
stats = await my_service.get_statistics()
```

### 数据库配置和环境变量

#### 环境变量配置
```bash
# 数据库配置（在 main.py 中读取）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=letcoding
DB_USER=postgres
DB_PASSWORD=your_password
DB_MAX_CONNECTIONS=20
DB_STALE_TIMEOUT=300
```

#### 配置服务使用
```python
# 在服务中获取数据库配置
from interfaces.service_interfaces import IConfigService

class MyService(Injectable):
    def __init__(self, config_service: IConfigService):
        self._config = config_service
    
    def get_database_info(self):
        """获取数据库配置信息"""
        db_config = self._config.get_database_config()
        database_url = self._config.get_database_url()
        
        return {
            "config": db_config,
            "connection_url": database_url.replace(db_config["password"], "***")
        }
```

### 数据库连接管理

#### 连接状态检查
```python
class DatabaseHealthService(Injectable):
    def __init__(self, database_service: DatabaseService):
        self._db = database_service
    
    def check_database_health(self):
        """检查数据库健康状态"""
        is_connected = self._db.test_connection()
        db_info = self._db.get_database_info()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connection_details": db_info,
            "timestamp": datetime.now().isoformat()
        }
```

#### 连接池配置
```python
# 数据库服务自动管理连接池
# 通过环境变量配置：
# DB_MAX_CONNECTIONS=20  # 最大连接数
# DB_STALE_TIMEOUT=300    # 连接超时时间
```

### 数据库迁移和表管理

#### 创建表
```python
# 在应用启动时或部署脚本中
from models.db_models import create_tables

def initialize_database():
    """初始化数据库表"""
    try:
        create_tables()
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建表失败: {e}")

# 在 main.py 中调用
if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host='0.0.0.0', port=6173)
```

#### 删除表（开发环境）
```python
from models.db_models import drop_tables

def cleanup_database():
    """清理数据库表（仅开发环境）"""
    if os.getenv('ENVIRONMENT') == 'development':
        drop_tables()
        print("开发环境：数据库表已删除")
```

### 数据库操作最佳实践

#### 1. 异常处理
```python
async def safe_user_creation(username: str, email: str, password_hash: str):
    """安全的用户创建操作"""
    try:
        user = await self._db.create_user(username, email, password_hash)
        return {"success": True, "user": user}
    except ValueError as e:
        # 业务逻辑错误
        return {"success": False, "error": str(e)}
    except RuntimeError as e:
        # 数据库运行时错误
        logger.error(f"数据库错误: {e}")
        return {"success": False, "error": "服务器内部错误"}
    except Exception as e:
        # 未预期错误
        logger.error(f"未预期错误: {e}")
        return {"success": False, "error": "系统异常"}
```

#### 2. 事务处理
```python
# DatabaseService 内部自动处理事务
# 使用 with database.atomic(): 确保操作原子性
```

#### 3. 数据验证
```python
async def create_user_with_validation(username: str, email: str, password_hash: str):
    """带验证的用户创建"""
    # 输入验证
    if not username or len(username) < 3:
        raise ValueError("用户名长度至少3个字符")
    
    if not email or "@" not in email:
        raise ValueError("邮箱格式无效")
    
    if not password_hash or len(password_hash) < 8:
        raise ValueError("密码哈希无效")
    
    # 调用数据库服务
    return await self._db.create_user(username, email, password_hash)
```

#### 4. 分页查询
```python
async def get_user_executions_paginated(user_id: int, page: int = 1, page_size: int = 20):
    """分页获取用户执行记录"""
    offset = (page - 1) * page_size
    
    executions = await self._db.get_user_executions(
        user_id=user_id,
        limit=page_size,
        offset=offset
    )
    
    return {
        "executions": executions,
        "page": page,
        "page_size": page_size,
        "has_more": len(executions) == page_size
    }
```

### 性能优化建议

#### 1. 索引优化
```python
# 在模型中定义索引
class User(BaseModel):
    username = CharField(max_length=50, unique=True, index=True)
    email = CharField(max_length=100, unique=True, index=True)
    created_at = DateTimeField(index=True)  # 用于时间范围查询
```

#### 2. 查询优化
```python
# 使用 select_related 避免N+1查询
executions = (CodeExecution
             .select(CodeExecution, User)
             .join(User)
             .where(User.id == user_id))

# 使用只查询需要的字段
users = User.select(User.id, User.username, User.email)
```

#### 3. 批量操作
```python
# 批量插入
with database.atomic():
    for i in range(1000):
        User.create(username=f"user_{i}", email=f"user_{i}@example.com")
```

## 🔄 Redis 缓存服务使用

### Redis 服务概述

项目中使用独立的 Redis 服务来处理所有缓存需求，包括用户信息缓存、JWT 令牌管理、速率限制等。

### 基本使用方法

#### 依赖注入方式
```python
from interfaces.service_interfaces import IRedisService
from core.di_container import Injectable

class MyService(Injectable):
    def __init__(self, redis_service: IRedisService):
        self._redis = redis_service
    
    def cache_data(self, key: str, value: dict):
        # 设置缓存，1小时过期
        self._redis.set(key, value, ttl=3600)
    
    def get_cached_data(self, key: str):
        return self._redis.get(key)
```

#### 运行时注入方式
```python
from core.di_container import inject
from interfaces.service_interfaces import IRedisService

def my_function():
    redis_service = inject(IRedisService)
    
    # 检查连接状态
    if not redis_service.is_connected():
        redis_service.reconnect()
    
    # 使用缓存
    result = redis_service.get('my_key', default='default_value')
    return result
```

### 常用操作示例

#### 1. 基本键值操作
```python
# 设置字符串值（自动JSON序列化）
redis_service.set('user:123', {
    'id': 123,
    'name': '张三',
    'email': 'zhangsan@example.com'
}, ttl=3600)

# 获取值（自动JSON反序列化）
user_data = redis_service.get('user:123')

# 删除键
redis_service.delete('user:123')

# 检查键是否存在
if redis_service.exists('user:123'):
    print('用户数据存在')
```

#### 2. 计数器操作
```python
# 递增计数器（用户访问次数）
visit_count = redis_service.increment(f'visits:user:{user_id}')
print(f'用户 {user_id} 访问了 {visit_count} 次')

# 递减计数器
remaining_requests = redis_service.decrement(f'rate_limit:user:{user_id}')
```

#### 3. 集合操作
```python
# 添加用户到白名单
redis_service.set_add('whitelist', 'user_123', 'user_456')

# 检查用户是否在白名单中
if redis_service.set_is_member('whitelist', 'user_123'):
    print('用户在白名单中')

# 获取所有白名单用户
whitelist_users = redis_service.set_members('whitelist')

# 从白名单移除用户
redis_service.set_remove('whitelist', 'user_123')
```

#### 4. 列表操作
```python
# 添加日志到队列
redis_service.list_push('logs', {
    'timestamp': '2024-01-01T10:00:00',
    'level': 'INFO',
    'message': '用户登录'
})

# 获取最近的日志（FIFO）
recent_log = redis_service.list_pop('logs')

# 获取队列长度
log_count = redis_service.list_length('logs')

# 获取指定范围的日志
all_logs = redis_service.list_range('logs', 0, -1)
```

#### 5. TTL 管理
```python
# 设置键的过期时间
redis_service.expire('user:123', 1800)  # 30分钟后过期

# 检查键的剩余生存时间
remaining_seconds = redis_service.ttl('user:123')
if remaining_seconds > 0:
    print(f'键将在 {remaining_seconds} 秒后过期')
elif remaining_seconds == -1:
    print('键永不过期')
else:
    print('键不存在')
```

### 缓存设计模式

#### 1. Cache-Aside 模式
```python
def get_user_profile(user_id: str):
    cache_key = f'user_profile:{user_id}'
    
    # 先从缓存获取
    profile = redis_service.get(cache_key)
    if profile:
        return profile
    
    # 缓存未命中，从数据库获取
    profile = database_service.get_user_profile(user_id)
    
    # 写入缓存
    if profile:
        redis_service.set(cache_key, profile, ttl=3600)
    
    return profile
```

#### 2. Write-Through 模式
```python
def update_user_profile(user_id: str, profile_data: dict):
    # 更新数据库
    database_service.update_user_profile(user_id, profile_data)
    
    # 同时更新缓存
    cache_key = f'user_profile:{user_id}'
    redis_service.set(cache_key, profile_data, ttl=3600)
```

#### 3. 分布式锁
```python
def with_lock(lock_key: str, expire_time: int = 10):
    """分布式锁装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试获取锁
            lock_acquired = redis_service.set(
                lock_key, 
                'locked', 
                ttl=expire_time
            )
            
            if not lock_acquired:
                raise Exception('无法获取锁，请稍后重试')
            
            try:
                return func(*args, **kwargs)
            finally:
                # 释放锁
                redis_service.delete(lock_key)
        
        return wrapper
    return decorator

# 使用示例
@with_lock('user_update:123')
def update_user_data():
    # 执行需要加锁的操作
    pass
```

### 错误处理和重连

```python
class RobustCacheService:
    def __init__(self, redis_service: IRedisService):
        self._redis = redis_service
    
    def safe_get(self, key: str, default=None):
        """安全的获取操作，包含重连逻辑"""
        try:
            result = self._redis.get(key, default)
            return result
        except Exception as ex:
            logger.error(f"Redis 获取失败: {key}", ex)
            
            # 尝试重连
            if self._redis.reconnect():
                return self._redis.get(key, default)
            
            return default
    
    def safe_set(self, key: str, value, ttl=None):
        """安全的设置操作"""
        try:
            return self._redis.set(key, value, ttl)
        except Exception as ex:
            logger.error(f"Redis 设置失败: {key}", ex)
            return False
```

### Redis 配置和监控

#### 环境变量配置
```bash
# Redis 基本配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
REDIS_TIMEOUT=5  # 连接超时时间
```

#### 连接状态监控
```python
# 获取 Redis 服务器信息
redis_info = redis_service.info()
if redis_info:
    print(f"Redis 版本: {redis_info.get('redis_version')}")
    print(f"已用内存: {redis_info.get('used_memory_human')}")

# 检查连接状态
if redis_service.is_connected():
    print("Redis 连接正常")
else:
    print("Redis 连接断开，尝试重连...")
    redis_service.reconnect()
```

## 🔐 认证和授权开发

### 认证架构概述

项目实现了基于 OIDC 的第三方认证和 JWT 令牌认证系统，支持 GitHub OAuth 和自定义 OIDC 提供商。

### JWT 服务使用

#### 生成和验证令牌
```python
from services.jwt_service import JWTService
from models.auth_models import UserInfo

# 在服务中使用 JWT
class MyProtectedService(Injectable):
    def __init__(self, jwt_service: JWTService, redis_service: IRedisService):
        self._jwt = jwt_service
        self._redis = redis_service
    
    def authenticate_user(self, user_info: dict):
        """生成 JWT 令牌"""
        # 创建用户信息对象
        user = UserInfo(
            id=user_info['id'],
            username=user_info['username'],
            email=user_info['email'],
            provider=user_info['provider']
        )
        
        # 生成令牌
        tokens = self._jwt.generate_tokens(user.to_dict())
        return tokens.to_dict()
    
    def verify_token(self, token: str):
        """验证 JWT 令牌"""
        user_info = self._jwt.verify_access_token(token)
        return user_info
    
    def refresh_token(self, refresh_token: str):
        """刷新访问令牌"""
        new_tokens = self._jwt.refresh_access_token(refresh_token)
        return new_tokens.to_dict() if new_tokens else None
```

### 认证中间件使用

#### 在控制器中使用认证
```python
from flask import g
from middleware.auth_middleware import AuthMiddleware

@api.route('/protected')
class ProtectedController(Resource):
    @AuthMiddleware.require_auth
    def get(self):
        """需要认证的接口"""
        # 从 g 对象获取当前用户信息
        current_user = getattr(g, 'current_user', None)
        
        return {
            'message': f'你好，{current_user["username"]}!',
            'user_id': current_user['id']
        }

@api.route('/optional')
class OptionalAuthController(Resource):
    @AuthMiddleware.optional_auth
    def get(self):
        """可选认证的接口"""
        current_user = getattr(g, 'current_user', None)
        
        if current_user:
            return {'message': f'已登录用户：{current_user["username"]}'}
        else:
            return {'message': '游客访问'}

@api.route('/admin')
class AdminController(Resource):
    @AuthMiddleware.require_auth
    @AuthMiddleware.require_admin
    def get(self):
        """需要管理员权限的接口"""
        return {'message': '管理员专用接口'}
```

#### 速率限制中间件
```python
@api.route('/rate-limited')
class RateLimitedController(Resource):
    @AuthMiddleware.require_auth
    @AuthMiddleware.rate_limit(max_requests=100, window_seconds=3600)
    def post(self):
        """带速率限制的接口"""
        return {'message': '请求成功'}
```

### OIDC 服务集成

#### 支持的认证提供商
```python
from services.oidc_service import OIDCService

class MyAuthService(Injectable):
    def __init__(self, oidc_service: OIDCService):
        self._oidc = oidc_service
    
    def get_supported_providers(self):
        """获取支持的认证提供商"""
        return self._oidc.get_supported_providers()
    
    def initiate_oauth(self, provider: str, redirect_uri: str):
        """开始 OAuth 认证流程"""
        if not self._oidc.validate_provider(provider):
            raise ValueError(f'不支持的提供商: {provider}')
        
        auth_url = self._oidc.get_authorization_url(provider, redirect_uri)
        return auth_url
    
    def handle_callback(self, provider: str, code: str):
        """处理 OAuth 回调"""
        auth_result = self._oidc.authorize_callback(provider)
        
        if not auth_result:
            raise Exception('认证失败')
        
        return auth_result['user_info']
```

### 用户信息管理

#### 数据模型使用
```python
from models.auth_models import UserInfo, TokenResponse

# 创建用户信息
user = UserInfo(
    id='github_123456',
    username='john_doe',
    email='john@example.com',
    name='John Doe',
    avatar_url='https://avatars.githubusercontent.com/u/123456',
    provider='github'
)

# 转换为字典
user_dict = user.to_dict()

# 创建令牌响应
tokens = TokenResponse(
    access_token='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
    refresh_token='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
    expires_in=3600,
    user_info=user
)
```

## 🎮 控制器编写

### 控制器基本结构

```python
# controllers/my_controller.py
from flask import request
from flask_restx import Resource, Namespace, fields
from core.di_container import inject
from interfaces.service_interfaces import IMyService

# 创建命名空间
api = Namespace('my_module', description='我的模块相关操作')

# 定义请求模型
request_model = api.model('MyRequest', {
    'data': fields.String(required=True, description='要处理的数据'),
})

# 定义响应模型
response_model = api.model('MyResponse', {
    'result': fields.String(description='处理结果'),
    'success': fields.Boolean(description='是否成功'),
})

@api.route('/process')
class MyController(Resource):
    @api.expect(request_model)
    @api.doc('process_data')
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request')
    def post(self):
        """处理数据"""
        # 注入服务
        my_service = inject(IMyService)
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return {'error': '请求体不能为空'}, 400
        
        input_data = data.get('data', '')
        if not input_data:
            return {'error': 'data参数不能为空'}, 400
        
        try:
            # 调用服务
            result = my_service.process_data(input_data)
            
            return {
                'result': result,
                'success': True
            }, 200
            
        except Exception as ex:
            return {
                'error': f'处理失败: {str(ex)}',
                'success': False
            }, 500

@api.route('/status')
class StatusController(Resource):
    @api.doc('get_service_status')
    @api.response(200, 'Success')
    def get(self):
        """获取服务状态"""
        my_service = inject(IMyService)
        status = my_service.get_status()
        
        return {
            'status': 'healthy' if status else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }, 200
```

### 控制器编写要点

1. **依赖注入**: 使用 `inject()` 函数获取服务
2. **参数验证**: 始终验证输入参数
3. **错误处理**: 统一的错误响应格式
4. **API文档**: 使用 flask-restx 的装饰器
5. **HTTP状态码**: 返回正确的状态码

## 🛣️ 路由注册

### 步骤1：在控制器中定义命名空间

```python
# 在控制器文件顶部
from flask_restx import Namespace

api = Namespace('module_name', description='模块描述')
```

### 步骤2：在主应用中注册

```python
# 在 main.py 中
from controllers.my_controller import api as my_api

# 注册命名空间
api.add_namespace(my_api, path='/my-module')
```

### 路由设计原则

1. **RESTful风格**: 使用标准HTTP方法
2. **资源导向**: URL应该表示资源
3. **版本控制**: 可考虑添加版本前缀
4. **清晰简洁**: 避免过深的路径嵌套

## 🚀 完整开发流程示例

### 需求：添加一个用户信息服务

#### 1. 定义接口
```python
# interfaces/service_interfaces.py 添加
@dataclass
class UserProfile:
    id: int
    name: str
    email: str

class IUserService(ABC):
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[UserProfile]:
        pass
    
    @abstractmethod
    def create_user(self, name: str, email: str) -> UserProfile:
        pass
```

#### 2. 实现服务
```python
# services/user_service.py
from typing import Optional, Dict
from interfaces.service_interfaces import IUserService, UserProfile
from core.di_container import Injectable

class UserService(IUserService, Injectable):
    def __init__(self, logger_service):
        self._logger = logger_service
        self._users: Dict[int, UserProfile] = {}
        self._next_id = 1
    
    def get_user(self, user_id: int) -> Optional[UserProfile]:
        return self._users.get(user_id)
    
    def create_user(self, name: str, email: str) -> UserProfile:
        user = UserProfile(
            id=self._next_id,
            name=name,
            email=email
        )
        self._users[self._next_id] = user
        self._next_id += 1
        
        self._logger.info(f"创建用户: {user}")
        return user
```

#### 3. 注册服务
```python
# core/service_config.py
from services.user_service import UserService
from interfaces.service_interfaces import IUserService

def service_configurator(container):
    # ... 其他注册 ...
    container.register_singleton(IUserService, UserService)
```

#### 4. 创建控制器
```python
# controllers/user_controller.py
from flask import request
from flask_restx import Resource, Namespace, fields
from core.di_container import inject
from interfaces.service_interfaces import IUserService

api = Namespace('users', description='用户管理')

user_model = api.model('User', {
    'name': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
})

@api.route('')
class UserController(Resource):
    @api.expect(user_model)
    def post(self):
        """创建用户"""
        user_service = inject(IUserService)
        data = request.get_json()
        
        user = user_service.create_user(data['name'], data['email'])
        return user.__dict__, 201

@api.route('/<int:user_id>')
class UserDetailController(Resource):
    def get(self, user_id):
        """获取用户详情"""
        user_service = inject(IUserService)
        user = user_service.get_user(user_id)
        
        if not user:
            return {'error': '用户不存在'}, 404
        
        return user.__dict__
```

#### 5. 注册路由
```python
# main.py 添加
from controllers.user_controller import api as user_api

api.add_namespace(user_api, path='/api/v1/users')
```

## ❓ 常见问题和最佳实践

### 常见问题

#### Q: 如何选择服务的生命周期？
**A**: 
- 配置服务、日志服务、Redis服务 → Singleton
- 数据库上下文、请求会话 → Scoped  
- 临时计算服务 → Transient

#### Q: 如何处理循环依赖？
**A**: 
- 重新设计服务职责，避免循环依赖
- 使用事件驱动模式
- 提取共同依赖到第三方服务

#### Q: Redis 连接失败怎么办？
**A**: 
- Redis 服务内置了自动重连机制
- 使用 `redis_service.is_connected()` 检查连接状态
- 使用 `redis_service.reconnect()` 手动重连
- 对于非关键缓存，考虑降级处理

#### Q: 如何处理 Redis 中的敏感数据？
**A**: 
- 对敏感数据进行加密后再存储
- 使用合适的键命名避免敏感信息泄露
- 设置适当的 TTL 确保数据及时过期
- 定期清理不再需要的数据

#### Q: 数据库连接失败怎么办？
**A**: 
- DatabaseService 内置了连接检查机制
- 使用 `database_service.test_connection()` 测试连接
- 检查数据库配置是否正确（环境变量）
- 确保数据库服务正在运行
- 查看数据库日志排查问题

#### Q: 如何进行数据库迁移？
**A**: 
- 使用 Peewee 的 `pwiz` 工具生成迁移脚本
- 在开发环境中谨慎使用 `drop_tables()`
- 生产环境建议使用专业的数据库迁移工具
- 备份重要数据后再执行迁移操作

#### Q: 如何创建新的数据库服务？
**A**: 
- 创建新的服务类继承 DatabaseService 和 Injectable
- 实现特定表的业务逻辑方法
- 在 service_config.py 中注册新服务
- 使用依赖注入获取服务实例

#### Q: 数据库服务之间如何协作？
**A**: 
- 通过依赖注入获取其他服务实例
- 使用统一的事务管理
- 避免循环依赖，必要时通过事件或共享服务解耦
- 利用 DatabaseService 提供的基础 CRUD 操作

#### Q: 如何处理数据库中的敏感信息？
**A**: 
- 密码等敏感字段使用哈希存储
- 在 `to_dict()` 方法中排除敏感字段
- 数据库连接字符串中的密码使用环境变量
- 限制数据库访问权限，使用最小权限原则

#### Q: 数据库性能优化有哪些方法？
**A**: 
- 为经常查询的字段添加索引
- 使用 `select_related()` 避免N+1查询
- 合理使用分页查询
- 考虑使用数据库连接池
- 定期分析和优化慢查询
- 使用专门的表服务减少不必要的字段查询
- 在服务层实现查询优化和缓存策略

#### Q: 模块化数据库服务有什么优势？
**A**: 
- **单一职责**: 每个服务专注于一个表的业务逻辑
- **易于维护**: 修改某个表的业务逻辑不会影响其他服务
- **便于测试**: 可以独立测试每个服务
- **代码复用**: DatabaseService 提供通用 CRUD 操作
- **团队协作**: 不同开发者可以并行开发不同的表服务
- **扩展性**: 新增表只需创建对应的服务类

#### Q: JWT 令牌被盗用怎么办？
**A**: 
- 实现令牌黑名单机制（项目中已实现）
- 使用较短的访问令牌过期时间
- 监控异常的令牌使用模式
- 支持强制用户重新登录

#### Q: 如何进行单元测试？
**A**: 
```python
# 测试 Redis 服务
def test_my_service_with_redis():
    # 创建模拟 Redis 服务
    mock_redis = Mock(spec=IRedisService)
    mock_redis.get.return_value = "cached_value"
    
    # 创建测试服务
    service = MyService(mock_redis, mock_config, mock_logger)
    
    # 测试方法
    result = service.get_cached_data("test_key")
    
    # 验证调用
    mock_redis.get.assert_called_once_with("test_key")
    assert result == "cached_value"

# 集成测试使用真实 Redis
def test_integration_with_redis():
    # 使用测试 Redis 数据库
    redis_service = RedisService(test_config, test_logger)
    redis_service.flushdb()  # 清空测试数据库
    
    # 测试缓存操作
    redis_service.set("test_key", "test_value", ttl=60)
    result = redis_service.get("test_key")
    
    assert result == "test_value"
```

### 最佳实践

1. **命名规范**
   - 接口: `IServiceName`
   - 实现: `ServiceName`
   - 控制器: `ServiceNameController`
   
2. **模块组织**
   - 抽象接口放在 `interfaces/` 目录
   - 数据模型放在 `models/` 目录
   - 服务实现放在 `services/` 目录
   - 控制器放在 `controllers/` 目录
   - 数据库模型继承 BaseModel，使用 Peewee ORM 规范

2. **错误处理**
   ```python
   try:
       result = service.process(data)
       return {'success': True, 'data': result}
   except BusinessException as ex:
       return {'error': str(ex)}, 400
   except Exception as ex:
       logger.error("未预期错误", ex)
       return {'error': '内部服务器错误'}, 500
   ```

3. **配置管理**
   ```python
   # 使用配置服务而不是直接访问环境变量
   timeout = config_service.get_config('TIMEOUT', 30)
   ```

4. **日志记录**
   ```python
   # 在关键操作前后记录日志
   logger.info("开始处理请求")
   try:
       result = service.process()
       logger.info(f"处理成功: {result}")
       return result
   except Exception as ex:
       logger.error("处理失败", ex)
       raise
   ```

5. **数据库设计**
   ```python
   # 使用 BaseModel 提供统一的基础字段
   # 在 to_dict() 中排除敏感信息
   # 为经常查询的字段添加索引
   # 使用合适的字段类型和约束
   # 为每个表创建专门的服务类继承 DatabaseService
   # 在服务层实现业务逻辑，保持模型类简洁
   ```

6. **API设计**
   - 使用复数名词表示资源集合
   - 使用HTTP状态码表示操作结果
   - 提供清晰的错误信息

## 📝 总结

通过本教程，你应该掌握了：
- 依赖注入的概念和使用方法
- 服务开发的完整流程
- 数据库服务的设计和使用
- Redis 缓存服务的使用和最佳实践
- 认证和授权系统的开发
- 控制器的编写规范
- 路由注册的方式

### 🎯 下一步学习建议

1. **实践项目**: 尝试添加一个新的业务模块，完整地走一遍开发流程
2. **数据库进阶**: 学习数据库高级特性，如事务处理、索引优化、分表分库等
3. **性能优化**: 学习 Redis 高级特性，如管道、发布订阅等
4. **安全加固**: 了解更多认证安全知识，如 CSRF 防护、令牌刷新策略、数据库安全
5. **监控部署**: 学习如何监控数据库、Redis 和应用的性能指标
6. **测试完善**: 为现有代码编写完整的单元测试和集成测试

记住，好的代码架构需要持续的实践和改进。建议从小功能开始练习，逐步掌握这些概念。

祝你编码愉快！🎉