"""
数据库服务基类模块

提供通用的数据库连接管理和 CRUD（增删改查）操作封装。
其他业务服务（如 UserService）可以继承此类获得基本的数据库操作能力。

功能：
- 基于 Peewee ORM 和连接池的 PostgreSQL 连接管理
- 通用的创建、查询、更新、删除操作
- 事务支持（atomic）
- 连接测试和状态监控
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from peewee import DoesNotExist, IntegrityError, fn, Model, Database
from playhouse.pool import PooledPostgresqlExtDatabase
from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService


class DatabaseService(Injectable):
    """
    数据库服务基类

    提供数据库连接管理和通用 CRUD 操作。
    子类可以通过继承获得数据库操作能力，并在此基础上添加业务特定的方法。

    使用方式：
        class UserService(DatabaseService):
            async def get_user(self, user_id):
                return await self.get_by_id(User, user_id)
    """

    def __init__(self, config_service: IConfigService):
        """
        初始化数据库服务

        Args:
            config_service: 配置服务，用于读取数据库连接参数
        """
        self._config_service = config_service
        self._database: Optional[Database] = None
        self._ensure_connection()

    def _get_database(self) -> Database:
        """
        获取 PostgreSQL 数据库连接池实例

        惰性初始化：首次调用时根据 ConfigService 的配置创建连接池。
        """
        if self._database is None:
            db_config = self._config_service.get_database_config()
            self._database = PooledPostgresqlExtDatabase(
                db_config["database"],
                user=db_config["username"],
                password=db_config["password"],
                host=db_config["host"],
                port=db_config["port"],
                max_connections=db_config["max_connections"],
                stale_timeout=db_config["stale_timeout"]
            )
        return self._database

    def _ensure_connection(self):
        """确保数据库连接可用，如果不可用则尝试建立新连接"""
        try:
            db = self._get_database()
            if not db.is_connection_usable():
                db.connect()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    # ============================================================
    # 通用 CRUD（增删改查）操作
    # ============================================================

    async def create(self, model_class: type, **kwargs) -> Dict[str, Any]:
        """
        创建一条新记录

        Args:
            model_class: Peewee 模型类
            **kwargs: 字段名与值的键值对

        Returns:
            新创建记录的字典表示

        Raises:
            ValueError: 如果违反唯一约束等数据完整性错误
            RuntimeError: 其他数据库操作错误
        """
        try:
            with self._get_database().atomic():
                instance = model_class.create(**kwargs)
                return instance.to_dict()
        except IntegrityError as e:
            raise ValueError(f"创建失败: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"创建记录时发生错误: {e}")

    async def get_by_id(self, model_class: type, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据主键 ID 获取单条记录

        Args:
            model_class: Peewee 模型类
            record_id: 记录的主键 ID

        Returns:
            记录的字典表示，不存在时返回 None
        """
        try:
            instance = model_class.get_by_id(record_id)
            return instance.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取记录时发生错误: {e}")

    async def update(self, model_class: type, record_id: int, **kwargs) -> bool:
        """
        更新指定记录

        Args:
            model_class: Peewee 模型类
            record_id: 要更新的记录的主键 ID
            **kwargs: 要更新的字段与值

        Returns:
            是否更新成功（True 表示至少有一行被更新）
        """
        try:
            with self._get_database().atomic():
                query = model_class.update(**kwargs).where(model_class.id == record_id)
                return query.execute() > 0
        except Exception as e:
            raise RuntimeError(f"更新记录时发生错误: {e}")

    async def delete(self, model_class: type, record_id: int) -> bool:
        """
        删除指定记录

        Args:
            model_class: Peewee 模型类
            record_id: 要删除的记录的主键 ID

        Returns:
            是否删除成功（True 表示至少有一行被删除）
        """
        try:
            with self._get_database().atomic():
                query = model_class.delete().where(model_class.id == record_id)
                return query.execute() > 0
        except Exception as e:
            raise RuntimeError(f"删除记录时发生错误: {e}")

    async def list_all(self, model_class: type, limit: int = 50, offset: int = 0, order_by=None) -> List[Dict[str, Any]]:
        """
        分页查询所有记录

        Args:
            model_class: Peewee 模型类
            limit: 每页数量（默认 50）
            offset: 偏移量（默认 0）
            order_by: 排序条件（可选）

        Returns:
            记录字典列表
        """
        try:
            query = model_class.select()
            if order_by:
                query = query.order_by(order_by)
            query = query.limit(limit).offset(offset)

            return [instance.to_dict() for instance in query]
        except Exception as e:
            raise RuntimeError(f"查询列表时发生错误: {e}")

    async def count(self, model_class: type) -> int:
        """
        统计模型的总记录数

        Args:
            model_class: Peewee 模型类

        Returns:
            记录总数
        """
        try:
            return model_class.select().count()
        except Exception as e:
            raise RuntimeError(f"计数时发生错误: {e}")

    # ============================================================
    # 数据库管理操作
    # ============================================================

    def test_connection(self) -> bool:
        """测试数据库连接是否正常（执行 SELECT 1）"""
        try:
            db = self._get_database()
            db.execute_sql("SELECT 1")
            return True
        except Exception:
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库连接信息

        Returns:
            包含数据库名称、主机、端口和连接状态的字典
        """
        try:
            db = self._get_database()
            return {
                "database": db.database,
                "host": db.connect_kwargs.get("host", "localhost"),
                "port": db.connect_kwargs.get("port", 5432),
                "is_connected": not db.is_closed() and db.is_connection_usable()
            }
        except Exception as e:
            return {"error": str(e)}

    def close(self):
        """关闭数据库连接（如果当前是打开状态）"""
        db = self._get_database()
        if not db.is_closed():
            db.close()
