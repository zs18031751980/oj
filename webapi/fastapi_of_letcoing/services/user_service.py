"""
用户服务模块

提供与用户相关的所有数据库操作，继承自 DatabaseService 获得通用 CRUD 能力。

主要功能：
1. 用户注册与查询（通过用户名、邮箱、ID 查找）
2. 第三方登录用户查找与创建（find_or_create_user）
3. 用户密码管理（更新密码、密码哈希查询）
4. 用户状态管理（激活/停用）
5. 用户信息更新与搜索
6. 最后登录时间跟踪
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from peewee import DoesNotExist, IntegrityError, fn   # Peewee ORM 工具

from services.database_service import DatabaseService  # 数据库服务基类
from models.db_models import User                       # 用户 ORM 模型
from core.di_container import Injectable
from utils.role_utils import normalize_role

BEIJING_TZ = timezone(timedelta(hours=8))


class UserService(DatabaseService, Injectable):
    """
    用户服务类

    提供用户相关的业务逻辑操作，继承 DatabaseService 获得通用的
    create、get_by_id、update、delete 等能力。

    特别注意：
    - _user_with_password_hash_dict 方法返回包含密码哈希的数据，仅用于认证流程
    - to_dict() 方法会自动排除 password_hash 字段
    """

    def _user_with_password_hash_dict(self, user: User) -> Dict[str, Any]:
        """
        将用户 ORM 模型转换为包含密码哈希的认证数据字典

        此方法返回的数据包含敏感信息（password_hash），
        仅限在密码验证等认证场景中使用。

        Args:
            user: 用户 ORM 实例

        Returns:
            包含所有字段（含 password_hash）的用户信息字典
        """
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'is_active': user.is_active,
            'role': user.role,
            'theme_preference': user.theme_preference,
            'provider': user.provider,
            'provider_id': user.provider_id,
            'avatar_url': user.avatar_url,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
        }

    # ============================================================
    # 用户创建
    # ============================================================

    async def create_user(self, username: str, password_hash: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        创建新的本地用户

        Args:
            username: 用户名
            password_hash: 密码的哈希值
            email: 邮箱地址（可选）

        Returns:
            新创建用户的字典表示

        Raises:
            ValueError: 用户名或邮箱已存在
        """
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

    # ============================================================
    # 用户查询
    # ============================================================

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据用户 ID 查询用户信息"""
        return await self.get_by_id(User, user_id)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名查询用户信息"""
        try:
            user = User.get(User.username == username)
            return user.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户时发生错误: {e}")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱地址查询用户信息"""
        try:
            user = User.get(User.email == email)
            return user.to_dict()
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户时发生错误: {e}")

    # ============================================================
    # 用户信息更新
    # ============================================================

    async def update_user_last_login(self, user_id: int) -> bool:
        """更新用户的最后登录时间为当前时间"""
        return await self.update(User, user_id, last_login=datetime.now(BEIJING_TZ))

    async def update_user_info(self, user_id: int, **kwargs) -> bool:
        """
        更新用户信息

        只允许更新以下安全字段：username、email、is_active

        Args:
            user_id: 用户 ID
            **kwargs: 要更新的字段键值对

        Returns:
            是否更新成功
        """
        allowed_fields = {'username', 'email', 'is_active', 'theme_preference'}
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_data:
            return False

        return await self.update(User, user_id, **update_data)

    async def deactivate_user(self, user_id: int) -> bool:
        """停用用户账号（设置 is_active=False）"""
        return await self.update(User, user_id, is_active=False)

    async def activate_user(self, user_id: int) -> bool:
        """激活用户账号（设置 is_active=True）"""
        return await self.update(User, user_id, is_active=True)

    async def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """更新用户密码哈希"""
        return await self.update(User, user_id, password_hash=password_hash)

    # ============================================================
    # 用户列表与搜索
    # ============================================================

    async def list_users(self, limit: int = 50, offset: int = 0, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户列表（分页，按创建时间倒序）

        Args:
            limit: 每页数量（默认 50）
            offset: 偏移量（默认 0）
            active_only: 是否只返回激活状态的用户

        Returns:
            用户信息字典列表
        """
        try:
            query = User.select()
            if active_only:
                query = query.where(User.is_active == True)

            query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)

            return [user.to_dict() for user in query]
        except Exception as e:
            raise RuntimeError(f"获取用户列表时发生错误: {e}")

    async def search_users(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        根据关键词搜索用户（匹配用户名或邮箱）

        Args:
            keyword: 搜索关键词
            limit: 最大返回数量（默认 20）

        Returns:
            匹配的用户信息字典列表
        """
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
        """
        统计用户数量

        Args:
            active_only: 是否只统计激活状态的用户

        Returns:
            用户总数
        """
        try:
            query = User.select()
            if active_only:
                query = query.where(User.is_active == True)
            return query.count()
        except Exception as e:
            raise RuntimeError(f"统计用户数量时发生错误: {e}")

    # ============================================================
    # 认证相关（获取含密码哈希的用户信息）
    # ============================================================

    async def get_user_with_password_hash(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户 ID 获取包含密码哈希的认证信息

        Args:
            user_id: 用户 ID

        Returns:
            包含 password_hash 的用户信息字典
        """
        try:
            user = User.get_by_id(user_id)
            return self._user_with_password_hash_dict(user)
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户认证信息时发生错误: {e}")

    async def get_user_with_password_hash_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取包含密码哈希的认证信息"""
        try:
            user = User.get(User.username == username)
            return self._user_with_password_hash_dict(user)
        except DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"获取用户认证信息时发生错误: {e}")

    async def get_user_with_password_hash_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名或邮箱获取包含密码哈希的认证信息

        支持大小写不敏感的匹配（先尝试精确匹配，再尝试大小写不敏感匹配）。

        Args:
            identifier: 用户名或邮箱地址

        Returns:
            包含 password_hash 的用户信息字典，未找到返回 None
        """
        try:
            normalized_identifier = (identifier or '').strip()
            if not normalized_identifier:
                return None

            # 先尝试精确匹配
            try:
                user = User.get(
                    (User.username == normalized_identifier)
                    | (User.email == normalized_identifier)
                )
            except DoesNotExist:
                # 精确匹配失败，尝试大小写不敏感匹配
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

    # ============================================================
    # 第三方登录用户管理
    # ============================================================

    async def find_or_create_user(self, provider: str, provider_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据第三方登录信息查找或创建用户

        流程：
        1. 根据 provider + provider_id 查找已有用户
        2. 如果找到，更新用户信息（用户名、邮箱、头像、角色）
        3. 如果未找到，创建新用户
        4. 处理用户名和邮箱的冲突（追加后缀或清空邮箱）

        Args:
            provider: 登录提供商（如 'github'）
            provider_id: 提供商侧的用户唯一标识
            user_info: 来自提供商的用户信息（包含 username、email、avatar_url 等）

        Returns:
             标准化的用户信息字典（不含 password_hash）
        """
        print(f"[USER_SYNC] find_or_create_user 被调用: provider={provider}, provider_id={provider_id}")
        try:
            # ----- 查找已有用户 -----
            try:
                user = User.get(
                    (User.provider == provider) &
                    (User.provider_id == provider_id)
                )

                # 更新用户信息（只更新有变化的字段）
                if user_info.get('username') and user.username != user_info['username']:
                    user.username = user_info['username']
                if user_info.get('email') and user.email != user_info['email']:
                    user.email = user_info['email']
                if user_info.get('avatar_url') and user.avatar_url != user_info['avatar_url']:
                    user.avatar_url = user_info['avatar_url']
                if user_info.get('role') and user.role != user_info['role']:
                    user.role = normalize_role(user_info['role'])

                user.last_login = datetime.now(BEIJING_TZ)
                user.save()

                print(f"用户登录成功: {user.id} ({provider})")
                return user.to_dict()

            except DoesNotExist:
                # ----- 创建新用户 -----
                username = user_info.get('username') or f"{provider}_{provider_id}"
                email = user_info.get('email') or None

                # 处理用户名冲突：在用户名后追加 provider_id
                try:
                    existing_user = User.get(User.username == username)
                    username = f"{username}_{provider_id}"
                except DoesNotExist:
                    pass

                # 处理邮箱冲突：清空邮箱（让用户后续自行绑定）
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
                    role=normalize_role(user_info.get('role', 'member')),
                    provider=provider,
                    provider_id=provider_id,
                    avatar_url=user_info.get('avatar_url'),
                    is_active=True,
                    last_login=datetime.now(BEIJING_TZ)
                )

                print(f"新用户注册成功: {user.id} ({provider})")
                return user.to_dict()

        except Exception as e:
            raise RuntimeError(f"查找或创建用户时发生错误: {e}")
