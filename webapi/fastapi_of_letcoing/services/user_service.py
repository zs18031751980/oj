"""
用户服务文件
提供用户相关的数据库操作
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from peewee import DoesNotExist, IntegrityError, fn

from services.database_service import DatabaseService
from models.db_models import User
from core.di_container import Injectable


class UserService(DatabaseService, Injectable):
    """用户服务类"""

    def _user_with_password_hash_dict(self, user: User) -> Dict[str, Any]:
        """将用户模型转换为包含密码哈希的认证数据。"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'is_active': user.is_active,
            'provider': user.provider,
            'provider_id': user.provider_id,
            'avatar_url': user.avatar_url,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
        }
    
    async def create_user(self, username: str, password_hash: str, email: Optional[str] = None) -> Dict[str, Any]:
        """创建用户"""
        try:
            user_data = await self.create(
                User,
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True
            )
            return user_data
        except ValueError as e:
            if "username" in str(e):
                raise ValueError("用户名已存在")
            elif "email" in str(e):
                raise ValueError("邮箱已存在")
            else:
                raise ValueError("创建用户失败")
        except Exception as e:
            raise RuntimeError(f"创建用户时发生错误: {e}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        return await self.get_by_id(User, user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            user = User.get(User.username == username)
            return user.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户时发生错误: {e}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        try:
            user = User.get(User.email == email)
            return user.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户时发生错误: {e}")
    
    async def update_user_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间"""
        return await self.update(User, user_id, last_login=datetime.now())
    
    async def update_user_info(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        # 过滤允许更新的字段
        allowed_fields = {'username', 'email', 'is_active'}
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_data:
            return False
        
        return await self.update(User, user_id, **update_data)
    
    async def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        return await self.update(User, user_id, is_active=False)
    
    async def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        return await self.update(User, user_id, is_active=True)
    
    async def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """更新用户密码"""
        return await self.update(User, user_id, password_hash=password_hash)
    
    async def list_users(self, limit: int = 50, offset: int = 0, active_only: bool = False) -> List[Dict[str, Any]]:
        """获取用户列表"""
        try:
            query = User.select()
            if active_only:
                query = query.where(User.is_active == True)
            
            query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
            
            return [user.to_dict() for user in query]
        except Exception as e:
            raise RuntimeError(f"获取用户列表时发生错误: {e}")
    
    async def search_users(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索用户"""
        try:
            search_pattern = f"%{keyword}%"
            query = (User.select()
                    .where((User.username.contains(search_pattern)) | 
                           (User.email.contains(search_pattern)))
                    .limit(limit))
            
            return [user.to_dict() for user in query]
        except Exception as e:
            raise RuntimeError(f"搜索用户时发生错误: {e}")
    
    async def count_users(self, active_only: bool = False) -> int:
        """统计用户数量"""
        try:
            query = User.select()
            if active_only:
                query = query.where(User.is_active == True)
            return query.count()
        except Exception as e:
            raise RuntimeError(f"统计用户数量时发生错误: {e}")
    
    async def get_user_with_password_hash(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取包含密码哈希的用户信息（用于认证）"""
        try:
            user = User.get_by_id(user_id)
            return self._user_with_password_hash_dict(user)
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户认证信息时发生错误: {e}")
    
    async def get_user_with_password_hash_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取包含密码哈希的用户信息"""
        try:
            user = User.get(User.username == username)
            return self._user_with_password_hash_dict(user)
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户认证信息时发生错误: {e}")

    async def get_user_with_password_hash_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """根据用户名或邮箱获取包含密码哈希的用户信息"""
        try:
            normalized_identifier = (identifier or '').strip()
            if not normalized_identifier:
                return None

            try:
                user = User.get(
                    (User.username == normalized_identifier)
                    | (User.email == normalized_identifier)
                )
            except DoesNotExist:
                lowered_identifier = normalized_identifier.lower()
                user = User.get(
                    (fn.LOWER(User.username) == lowered_identifier)
                    | (fn.LOWER(User.email) == lowered_identifier)
                )

            return self._user_with_password_hash_dict(user)
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户认证信息时发生错误: {e}")
    
    async def find_or_create_user(self, provider: str, provider_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据第三方登录信息查找或创建用户
        
        Args:
            provider: 登录提供商 (如 'github', 'oidc-provider')
            provider_id: 提供商的用户ID
            user_info: 用户信息字典
            
        Returns:
            用户信息字典
        """
        try:
            # 尝试根据provider和provider_id查找用户
            try:
                user = User.get(
                    (User.provider == provider) & 
                    (User.provider_id == provider_id)
                )
                
                # 更新用户信息
                if user_info.get('username') and user.username != user_info['username']:
                    user.username = user_info['username']
                if user_info.get('email') and user.email != user_info['email']:
                    user.email = user_info['email']
                if user_info.get('avatar_url') and user.avatar_url != user_info['avatar_url']:
                    user.avatar_url = user_info['avatar_url']
                
                user.last_login = datetime.now()
                user.save()
                
                print(f"用户登录成功: {user.id} ({provider})")
                return user.to_dict()
                
            except DoesNotExist:
                # 用户不存在，创建新用户
                username = user_info.get('username') or f"{provider}_{provider_id}"
                email = user_info.get('email')
                
                # 检查用户名是否已存在
                try:
                    existing_user = User.get(User.username == username)
                    username = f"{username}_{provider_id}"
                except DoesNotExist:
                    pass
                
                # 检查邮箱是否已存在
                if email:
                    try:
                        existing_user = User.get(User.email == email)
                        email = None
                    except DoesNotExist:
                        pass
                
                user = User.create(
                    username=username,
                    email=email,
                    password_hash=None,
                    provider=provider,
                    provider_id=provider_id,
                    avatar_url=user_info.get('avatar_url'),
                    is_active=True,
                    last_login=datetime.now()
                )
                
                print(f"新用户注册成功: {user.id} ({provider})")
                return user.to_dict()
                
        except Exception as e:
            raise RuntimeError(f"查找或创建用户时发生错误: {e}")
