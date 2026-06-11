"""
数据库服务基类
提供数据库连接和基础操作
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from peewee import DoesNotExist, IntegrityError, fn, Model, Database
from playhouse.pool import PooledPostgresqlExtDatabase
from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService


class DatabaseService(Injectable):
    """数据库服务基类"""
    
    def __init__(self, config_service: IConfigService):
        """初始化数据库服务"""
        self._config_service = config_service
        self._database: Optional[Database] = None
        self._ensure_connection()
    
    def _get_database(self) -> Database:
        """获取数据库连接实例"""
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
        """确保数据库连接正常"""
        try:
            db = self._get_database()
            if not db.is_connection_usable():
                db.connect()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    # 通用CRUD操作
    async def create(self, model_class: type, **kwargs) -> Dict[str, Any]:
        """通用创建操作"""
        try:
            with self._get_database().atomic():
                instance = model_class.create(**kwargs)
                return instance.to_dict()
        except IntegrityError as e:
            raise ValueError(f"创建失败: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"创建记录时发生错误: {e}")
    
    async def get_by_id(self, model_class: type, record_id: int) -> Optional[Dict[str, Any]]:
        """通用根据ID获取记录"""
        try:
            instance = model_class.get_by_id(record_id)
            return instance.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取记录时发生错误: {e}")
    
    async def update(self, model_class: type, record_id: int, **kwargs) -> bool:
        """通用更新操作"""
        try:
            with self._get_database().atomic():
                query = model_class.update(**kwargs).where(model_class.id == record_id)
                return query.execute() > 0
        except Exception as e:
            raise RuntimeError(f"更新记录时发生错误: {e}")
    
    async def delete(self, model_class: type, record_id: int) -> bool:
        """通用删除操作"""
        try:
            with self._get_database().atomic():
                query = model_class.delete().where(model_class.id == record_id)
                return query.execute() > 0
        except Exception as e:
            raise RuntimeError(f"删除记录时发生错误: {e}")
    
    async def list_all(self, model_class: type, limit: int = 50, offset: int = 0, order_by=None) -> List[Dict[str, Any]]:
        """通用列表查询"""
        try:
            query = model_class.select()
            if order_by:
                query = query.order_by(order_by)
            query = query.limit(limit).offset(offset)
            
            return [instance.to_dict() for instance in query]
        except Exception as e:
            raise RuntimeError(f"查询列表时发生错误: {e}")
    
    async def count(self, model_class: type) -> int:
        """通用计数操作"""
        try:
            return model_class.select().count()
        except Exception as e:
            raise RuntimeError(f"计数时发生错误: {e}")
    
    # 数据库管理操作
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            db = self._get_database()
            db.execute_sql("SELECT 1")
            return True
        except Exception:
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
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
        """关闭数据库连接"""
        db = self._get_database()
        if not db.is_closed():
            db.close()
