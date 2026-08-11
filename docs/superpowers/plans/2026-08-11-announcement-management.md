# 公告管理与身份同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通数据库公告的公开读取和部长级管理工作流，并在身份登录时原地同步用户资料、账号状态、最后登录时间及只升不降的角色。

**Architecture:** 后端继续使用 Peewee `User`、`Announcement` 模型和 Flask-RESTX 命名空间，新增纯函数处理身份状态并以数据库角色作为写权限最终依据。前端公开页与管理页统一调用公告 API，路由守卫使用可测试的权限决策函数，Markdown 预览复用正式 `MarkdownComponent`。

**Tech Stack:** Python 3.11、Flask 3.1、Flask-RESTX、Peewee、标准库 `unittest`、Vue 3.5、TypeScript 5.9、Pinia、Vue Router、Naive UI、Node 24 test runner、Vite 7。

## Global Constraints

- `users.id` 和现有公告 `id` 必须原地保留，修改操作不得删除重建。
- 身份登录角色只升不降：`manager > staff > member`，本地手工提升不可被覆盖。
- 身份账号状态仅在声明明确存在且可识别时同步；缺失或无法识别时保留本地值。
- 公告写入、草稿读取仅允许 `manager`；后端权限校验是最终边界。
- 公开接口不得泄露草稿。
- Markdown 编辑器桌面双栏、移动端上下排列，预览必须复用正式渲染组件。
- 不实现版本历史、协同编辑、附件上传、审批流或静态公告双写。
- 当前两个虚拟环境的 Python 启动器指向已失效的 WindowsApps Python；执行后端测试前需使用机器上的 Python 3.11 修复 `.venv`，不得在没有测试结果时宣称后端通过。

## File Map

- Create `webapi/fastapi_of_letcoing/utils/identity_utils.py`: 解析身份账号状态，不依赖 Flask 或数据库。
- Create `webapi/fastapi_of_letcoing/tests/test_identity_sync.py`: 身份状态、角色提升、用户原地更新测试。
- Modify `webapi/fastapi_of_letcoing/controllers/auth_controller.py`: 从提供方 JWT 提取状态、统一登录同步、停止记录完整声明。
- Modify `webapi/fastapi_of_letcoing/services/oidc_service.py`: OIDC 用户信息透传可识别账号状态。
- Modify `webapi/fastapi_of_letcoing/services/user_service.py`: 同步资料、账号状态、角色和 `last_login`，保持主键。
- Modify `webapi/fastapi_of_letcoing/models/auth_models.py`: 本站用户响应增加 `is_active` 和 `last_login`。
- Modify `webapi/fastapi_of_letcoing/services/jwt_service.py`: JWT 与缓存回退数据包含最新账号状态。
- Create `webapi/fastapi_of_letcoing/tests/test_announcement_controller.py`: 公告可见性、权限和主键测试。
- Modify `webapi/fastapi_of_letcoing/controllers/announcement_controller.py`: 公开/管理读取策略和写入校验。
- Create `webapp/letapp/src/utils/announcement-access.ts`: 路由权限和公告表单纯函数。
- Create `webapp/letapp/tests/announcement-access.test.ts`: Node 原生 TypeScript 单元测试。
- Modify `webapp/letapp/package.json`: 增加无新依赖的前端测试脚本。
- Modify `webapp/letapp/src/services/api.ts`: 管理列表认证参数和完整公告类型。
- Modify `webapp/letapp/src/router.ts`: 登录与 `manager` 路由保护。
- Create `webapp/letapp/src/pages/AccessDenied.vue`: 权限拒绝状态页。
- Modify `webapp/letapp/src/pages/Announcements.vue`: 公开公告页接入 API，并展示管理入口。
- Modify `webapp/letapp/src/pages/admin/Announcements.vue`: 管理列表、同渲染器预览、保存/删除状态。

---

### Task 1: 身份状态归一化与用户原地同步

**Files:**
- Create: `webapi/fastapi_of_letcoing/utils/identity_utils.py`
- Create: `webapi/fastapi_of_letcoing/tests/__init__.py`
- Create: `webapi/fastapi_of_letcoing/tests/test_identity_sync.py`
- Modify: `webapi/fastapi_of_letcoing/services/user_service.py:316-390`

**Interfaces:**
- Produces: `extract_account_status(source: Mapping[str, Any]) -> Optional[bool]`。
- Produces: `UserService.find_or_create_user(provider, provider_id, user_info)` 返回原地同步后的完整本地用户字典。

- [ ] **Step 1: 写身份状态纯函数的失败测试**

```python
from unittest import TestCase

from utils.identity_utils import extract_account_status


class ExtractAccountStatusTests(TestCase):
    def test_reads_boolean_status_claims(self):
        self.assertIs(extract_account_status({'enabled': True}), True)
        self.assertIs(extract_account_status({'is_active': False}), False)

    def test_reads_known_status_strings(self):
        self.assertIs(extract_account_status({'status': 'active'}), True)
        self.assertIs(extract_account_status({'account_status': 'disabled'}), False)

    def test_missing_or_unknown_status_preserves_local_value(self):
        self.assertIsNone(extract_account_status({}))
        self.assertIsNone(extract_account_status({'status': 'pending-review'}))
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_identity_sync.ExtractAccountStatusTests -v`

Expected: FAIL，错误包含 `No module named 'utils.identity_utils'`。

- [ ] **Step 3: 实现状态归一化纯函数**

```python
from typing import Any, Mapping, Optional

_TRUE_VALUES = {'active', 'enabled', 'normal', 'valid', '1', 'true'}
_FALSE_VALUES = {'inactive', 'disabled', 'locked', 'suspended', 'invalid', '0', 'false'}


def extract_account_status(source: Mapping[str, Any]) -> Optional[bool]:
    for field in ('is_active', 'active', 'enabled', 'status', 'account_status'):
        if field not in source:
            continue
        value = source[field]
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    return None
```

- [ ] **Step 4: 增加用户同步失败测试**

使用 `peewee.SqliteDatabase(':memory:')` 初始化 `database_proxy`，创建一个固定 `id` 的 `manager` 用户。测试调用 `await find_or_create_user(...)` 后：返回和数据库中的 `id` 不变、提供方 `member` 不会降级角色、`enabled=False` 会更新 `is_active`、`last_login` 非空。再加一例状态缺失时保留原 `is_active`。测试类完整夹具如下：

```python
from unittest import IsolatedAsyncioTestCase

from peewee import SqliteDatabase

from models.db_models import User, database_proxy
from services.user_service import UserService


class UserSyncTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.database = SqliteDatabase(':memory:')
        database_proxy.initialize(self.database)
        self.database.create_tables([User])

    def tearDown(self):
        self.database.drop_tables([User])
        self.database.close()

    async def test_existing_user_keeps_id_and_manual_role_while_syncing_status(self):
        original = User.create(
            username='leader', provider='iOSClub', provider_id='42',
            role='manager', is_active=True,
        )
        result = await UserService().find_or_create_user(
            'iOSClub', '42',
            {'username': 'leader-new', 'role': 'member', 'is_active': False},
        )
        refreshed = User.get_by_id(original.id)
        self.assertEqual(result['id'], original.id)
        self.assertEqual(refreshed.id, original.id)
        self.assertEqual(refreshed.role, 'manager')
        self.assertFalse(refreshed.is_active)
        self.assertIsNotNone(refreshed.last_login)

    async def test_missing_status_preserves_local_value(self):
        original = User.create(
            username='disabled', provider='iOSClub', provider_id='43',
            role='member', is_active=False,
        )
        await UserService().find_or_create_user(
            'iOSClub', '43', {'username': 'disabled', 'role': 'member'},
        )
        self.assertFalse(User.get_by_id(original.id).is_active)
```

- [ ] **Step 5: 运行同步测试并确认当前实现失败**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_identity_sync -v`

Expected: 状态断言失败，因为当前 `find_or_create_user` 不同步 `is_active`。

- [ ] **Step 6: 最小修改 `find_or_create_user`**

在查询到现有用户后构建更新值；角色继续使用 `pick_highest_role([user.role, incoming_role])`，状态仅在 `is_active` 键存在时赋值，最后在同一个 ORM 实例上 `save()`：

```python
incoming_status = user_info.get('is_active')
if isinstance(incoming_status, bool):
    user.is_active = incoming_status

if user_info.get('role'):
    user.role = pick_highest_role([user.role, user_info['role']])

user.last_login = datetime.now(BEIJING_TZ)
user.save()
```

更新用户名或邮箱前查询是否已被其他用户占用；冲突时保留本地字段，不创建新用户。

- [ ] **Step 7: 运行身份同步测试**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_identity_sync -v`

Expected: 全部 PASS。

- [ ] **Step 8: 提交身份同步核心**

```bash
git add webapi/fastapi_of_letcoing/utils/identity_utils.py webapi/fastapi_of_letcoing/tests webapi/fastapi_of_letcoing/services/user_service.py
git commit -m "feat: synchronize identity account state"
```

### Task 2: 登录数据流与本站 JWT 状态一致性

**Files:**
- Modify: `webapi/fastapi_of_letcoing/controllers/auth_controller.py:238-385,621-830`
- Modify: `webapi/fastapi_of_letcoing/services/oidc_service.py:615-700`
- Modify: `webapi/fastapi_of_letcoing/models/auth_models.py:53-93`
- Modify: `webapi/fastapi_of_letcoing/services/jwt_service.py:52-215`
- Modify: `webapi/fastapi_of_letcoing/tests/test_identity_sync.py`

**Interfaces:**
- Consumes: `extract_account_status(source)`。
- Produces: 登录响应、Redis 缓存和 JWT 回退载荷共同包含 `is_active`、`last_login`。

- [ ] **Step 1: 写 JWT 状态提取和载荷失败测试**

```python
def test_provider_claims_include_normalized_account_status(self):
    token = jwt.encode({'sub': '42', 'role': 'minister', 'enabled': False}, 'provider-secret')
    result = _user_info_from_provider_token('iOSClub', 'leader', token)
    self.assertEqual(result['role'], 'manager')
    self.assertIs(result['is_active'], False)
```

对 `JWTService.generate_tokens()` 使用内存 Redis 替身，解码访问令牌并断言 `is_active` 与 `last_login` 存在；清空缓存后调用 `verify_access_token()`，断言仍能从载荷恢复这两个字段。

- [ ] **Step 2: 运行测试并确认缺少状态字段**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_identity_sync -v`

Expected: FAIL，断言显示 `is_active` 或 `last_login` 缺失。

- [ ] **Step 3: 在提供方数据中透传规范化状态**

`_user_info_from_provider_token()` 和 `OIDCService._build_oidc_user_info()` 都调用：

```python
account_status = extract_account_status(claims_or_user_data)
if account_status is not None:
    normalized_user['is_active'] = account_status
```

删除完整 JWT claims 和完整密码登录响应日志，只记录提供方名称、稳定用户标识和已识别字段名。

- [ ] **Step 4: 扩展本站用户与 JWT 字段**

在 `UserInfo` 增加：

```python
is_active: bool = True
last_login: Optional[str] = None
```

`to_dict()` 返回这两个字段；`JWTService` 的 access、refresh 载荷以及缓存缺失回退字典均使用相同字段名。`_build_user_info()` 从同步后的本地字典填充它们。

- [ ] **Step 5: 统一 OAuth 和密码身份登录签发路径**

两个入口都调用 `_issue_tokens_for_provider_user()` 完成本地同步。同步结果 `is_active is False` 时抛出 `PermissionError('account is inactive')`；密码接口返回 `403`，浏览器 OAuth 回调重定向到现有错误回调且不携带本站令牌。

- [ ] **Step 6: 运行身份测试与语法检查**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_identity_sync -v`

Run: `D:\probject\oj\.venv\Scripts\python.exe -m py_compile controllers/auth_controller.py services/oidc_service.py services/user_service.py services/jwt_service.py models/auth_models.py utils/identity_utils.py`

Expected: 两条命令退出码均为 `0`。

- [ ] **Step 7: 提交登录一致性修改**

```bash
git add webapi/fastapi_of_letcoing/controllers/auth_controller.py webapi/fastapi_of_letcoing/services/oidc_service.py webapi/fastapi_of_letcoing/models/auth_models.py webapi/fastapi_of_letcoing/services/jwt_service.py webapi/fastapi_of_letcoing/tests/test_identity_sync.py
git commit -m "fix: issue tokens from synchronized user state"
```

### Task 3: 公告可见性、权限和 CRUD

**Files:**
- Create: `webapi/fastapi_of_letcoing/tests/test_announcement_controller.py`
- Modify: `webapi/fastapi_of_letcoing/controllers/announcement_controller.py`

**Interfaces:**
- Produces: `GET /announcement/` 默认仅已发布；`include_unpublished=true` 仅 `manager`。
- Produces: `POST`、`PUT`、`DELETE` 仅 `manager`，`PUT` 原地更新并保持 `id`。

- [ ] **Step 1: 创建真实 Flask 路由与 SQLite 测试夹具**

测试使用 `Flask(__name__)`、`flask_restx.Api(app)` 注册公告命名空间，`database_proxy` 绑定内存 SQLite，并仅替换外部 JWT 服务：

```python
class FakeJWTService:
    def verify_access_token(self, token):
        return {'id': int(token)} if token.isdigit() else None

    def refresh_cached_user(self, user_id, user_info):
        return None
```

- [ ] **Step 2: 写公开可见性和管理权限失败测试**

创建一条已发布公告和一条草稿，断言：匿名列表只有已发布公告；匿名草稿详情为 `404`；普通成员带 `include_unpublished=true` 返回 `403`；`manager` 返回两条。

```python
response = self.client.get('/announcement/')
self.assertEqual([item['id'] for item in response.get_json()], [published.id])
self.assertEqual(self.client.get(f'/announcement/{draft.id}').status_code, 404)
```

- [ ] **Step 3: 写 CRUD 与主键失败测试**

断言普通成员的三个写请求均为 `403`；`manager` 创建成功、修改后 `id` 等于修改前、删除后返回 `404`；空标题或空内容返回 `400`。

- [ ] **Step 4: 运行公告测试并确认当前行为失败**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_announcement_controller -v`

Expected: FAIL，当前匿名列表会包含草稿，且草稿详情可公开读取。

- [ ] **Step 5: 实现读取策略和输入校验**

列表查询逻辑：

```python
include_unpublished = request.args.get('include_unpublished', '').lower() == 'true'
if include_unpublished:
    manager = _require_manager()
    if isinstance(manager, tuple):
        return manager
    query = Announcement.select()
else:
    query = Announcement.select().where(Announcement.is_published == True)
```

详情遇到草稿时，仅在 `_require_manager()` 成功后返回；普通访问统一 `404`。`PUT` 对传入的 `title`、`content` 执行 `strip()` 后校验非空，只在原 ORM 实例上 `save()`。

- [ ] **Step 6: 运行公告测试和全部后端测试**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest tests.test_announcement_controller -v`

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: 全部 PASS。

- [ ] **Step 7: 提交公告后端**

```bash
git add webapi/fastapi_of_letcoing/controllers/announcement_controller.py webapi/fastapi_of_letcoing/tests/test_announcement_controller.py
git commit -m "feat: enforce announcement visibility and permissions"
```

### Task 4: 可测试的前端权限与 API 契约

**Files:**
- Create: `webapp/letapp/src/utils/announcement-access.ts`
- Create: `webapp/letapp/tests/announcement-access.test.ts`
- Create: `webapp/letapp/src/pages/AccessDenied.vue`
- Modify: `webapp/letapp/package.json`
- Modify: `webapp/letapp/src/services/api.ts:1-205`
- Modify: `webapp/letapp/src/router.ts`

**Interfaces:**
- Produces: `resolveManagerRoute(isAuthenticated, role) -> 'allow' | 'login' | 'forbidden'`。
- Produces: `announcementToForm(item) -> AnnouncementForm`。
- Produces: `listAnnouncements({ includeUnpublished?: boolean })`。

- [ ] **Step 1: 写前端纯函数失败测试并增加测试脚本**

```typescript
import assert from 'node:assert/strict';
import test from 'node:test';
import { announcementToForm, resolveManagerRoute } from '../src/utils/announcement-access.ts';

test('manager route requires authentication and manager role', () => {
  assert.equal(resolveManagerRoute(false, undefined), 'login');
  assert.equal(resolveManagerRoute(true, 'member'), 'forbidden');
  assert.equal(resolveManagerRoute(true, 'manager'), 'allow');
});

test('announcement form preserves the edited announcement id', () => {
  assert.deepEqual(
    announcementToForm({ id: 17, title: '通知', content: '# 正文', is_published: true }),
    { id: 17, title: '通知', content: '# 正文', permission: 'member', is_published: true },
  );
});
```

`package.json` 增加：

```json
"test": "node --experimental-strip-types --test tests/announcement-access.test.ts"
```

- [ ] **Step 2: 运行测试并确认模块不存在**

Run: `npm.cmd test`

Expected: FAIL，错误包含 `ERR_MODULE_NOT_FOUND`。

- [ ] **Step 3: 实现权限和表单纯函数**

```typescript
import type { AnnouncementData, AnnouncementForm } from '../services/api';

export type ManagerRouteDecision = 'allow' | 'login' | 'forbidden';

export const resolveManagerRoute = (
  isAuthenticated: boolean,
  role?: string,
): ManagerRouteDecision => {
  if (!isAuthenticated) return 'login';
  return role === 'manager' ? 'allow' : 'forbidden';
};

export const announcementToForm = (item: AnnouncementData): AnnouncementForm => ({
  id: item.id,
  title: item.title,
  content: item.content,
  permission: item.permission || 'member',
  is_published: item.is_published,
});
```

- [ ] **Step 4: 更新 API 契约**

将 `AnnouncementData.id`、`is_published` 设为服务端响应必填字段；新增完整表单类型。管理列表请求发送认证令牌：

```typescript
export interface AnnouncementData {
  id: number;
  title: string;
  content: string;
  permission?: string;
  is_published: boolean;
  published_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AnnouncementForm {
  id: number;
  title: string;
  content: string;
  permission: string;
  is_published: boolean;
}

export const listAnnouncements = (options: { includeUnpublished?: boolean } = {}) => {
  const includeUnpublished = options.includeUnpublished === true;
  return apiRequest<AnnouncementData[]>(
    `/announcement/${includeUnpublished ? '?include_unpublished=true' : ''}`,
    { skipAuth: !includeUnpublished },
  );
};
```

- [ ] **Step 5: 实现路由保护和拒绝访问页**

给 `/admin` 父路由添加 `meta: { requiresAuth: true, requiresManager: true }`，新增 `/access-denied`。守卫先调用 `authStore.restoreSession()`，再使用 `resolveManagerRoute()`；`login` 结果触发现有 iOSClub 登录，`forbidden` 结果重定向拒绝页。

`AccessDenied.vue` 使用现有图标与 Naive UI 按钮，提供返回公告页的明确命令，不暴露管理内容。

- [ ] **Step 6: 运行前端测试和类型检查**

Run: `npm.cmd test`

Run: `node --max-old-space-size=4096 .\node_modules\vue-tsc\bin\vue-tsc.js -b`

Expected: 两条命令退出码为 `0`。

- [ ] **Step 7: 提交前端权限契约**

```bash
git add webapp/letapp/package.json webapp/letapp/src/utils/announcement-access.ts webapp/letapp/tests/announcement-access.test.ts webapp/letapp/src/services/api.ts webapp/letapp/src/router.ts webapp/letapp/src/pages/AccessDenied.vue
git commit -m "feat: protect announcement management routes"
```

### Task 5: 公开公告页接入数据库 API

**Files:**
- Modify: `webapp/letapp/src/pages/Announcements.vue`
- Modify: `webapp/letapp/src/utils/announcement-access.ts`
- Modify: `webapp/letapp/tests/announcement-access.test.ts`

**Interfaces:**
- Consumes: `listAnnouncements()`、`getAnnouncement(id)`、`authStore.userRole`。
- Produces: URL 查询参数 `id=<number>` 驱动的公开列表和详情。

- [ ] **Step 1: 写公告排序与查询 ID 失败测试**

```typescript
test('published announcements sort newest first', () => {
  const sorted = sortAnnouncementsNewestFirst([
    { id: 1, title: '旧', content: '', is_published: true, updated_at: '2026-01-01' },
    { id: 2, title: '新', content: '', is_published: true, updated_at: '2026-02-01' },
  ]);
  assert.deepEqual(sorted.map((item) => item.id), [2, 1]);
});

test('announcement id parser rejects invalid values', () => {
  assert.equal(parseAnnouncementId('17'), 17);
  assert.equal(parseAnnouncementId('abc'), null);
  assert.equal(parseAnnouncementId('-1'), null);
});
```

- [ ] **Step 2: 运行测试并确认导出不存在**

Run: `npm.cmd test`

Expected: FAIL，缺少 `sortAnnouncementsNewestFirst` 或 `parseAnnouncementId` 导出。

- [ ] **Step 3: 实现纯函数并通过测试**

```typescript
export const parseAnnouncementId = (raw: unknown): number | null => {
  const value = Array.isArray(raw) ? raw[0] : raw;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
};

export const sortAnnouncementsNewestFirst = (items: AnnouncementData[]) =>
  [...items].sort((left, right) => {
    const leftTime = Date.parse(left.updated_at || left.published_at || left.created_at || '');
    const rightTime = Date.parse(right.updated_at || right.published_at || right.created_at || '');
    return rightTime - leftTime;
  });
```

Run: `npm.cmd test`

Expected: PASS。

- [ ] **Step 4: 将公开页由静态文件切换到 API**

删除 `ManifestItem`、front matter 解析和 `/announcements/manifest.json`、Markdown 文件 fetch。`onMounted` 调用 `listAnnouncements()`；详情通过 `getAnnouncement(currentId)` 加载，并把响应映射为：

```typescript
selectedContent.value = {
  title: announcement.title,
  date: announcement.published_at || announcement.created_at,
  content: announcement.content,
};
```

列表项使用 `item.id` 作为 key 和查询参数。新增独立 `listError`、`detailError` 与重试按钮，避免请求失败伪装为空列表。

- [ ] **Step 5: 增加 manager 管理入口**

```typescript
const canManageAnnouncements = computed(() => authStore.userRole === 'manager');
const openManager = () => router.push('/admin/announcements');
```

在公告页工具栏仅对 `canManageAnnouncements` 显示带设置图标的“管理公告”按钮。

- [ ] **Step 6: 运行前端测试与构建**

Run: `npm.cmd test`

Run: `npm.cmd run build`

Expected: 测试 PASS，构建退出码 `0`。

- [ ] **Step 7: 提交公开公告页**

```bash
git add webapp/letapp/src/pages/Announcements.vue webapp/letapp/src/utils/announcement-access.ts webapp/letapp/tests/announcement-access.test.ts
git commit -m "feat: load published announcements from api"
```

### Task 6: 公告管理编辑器与操作状态

**Files:**
- Modify: `webapp/letapp/src/pages/admin/Announcements.vue`
- Modify: `webapp/letapp/src/utils/announcement-access.ts`
- Modify: `webapp/letapp/tests/announcement-access.test.ts`

**Interfaces:**
- Consumes: `listAnnouncements({ includeUnpublished: true })`、CRUD API、`MarkdownComponent`。
- Produces: 桌面双栏/移动上下布局的真实渲染预览和防重复操作状态。

- [ ] **Step 1: 写编辑表单校验失败测试**

```typescript
test('announcement form requires trimmed title and markdown', () => {
  assert.equal(canSaveAnnouncement({ id: 0, title: ' ', content: '# 正文', permission: 'member', is_published: true }), false);
  assert.equal(canSaveAnnouncement({ id: 0, title: '通知', content: ' ', permission: 'member', is_published: true }), false);
  assert.equal(canSaveAnnouncement({ id: 0, title: '通知', content: '# 正文', permission: 'member', is_published: true }), true);
});
```

- [ ] **Step 2: 运行测试并确认导出不存在**

Run: `npm.cmd test`

Expected: FAIL，缺少 `canSaveAnnouncement`。

- [ ] **Step 3: 实现表单校验并通过测试**

```typescript
export const canSaveAnnouncement = (form: AnnouncementForm) =>
  Boolean(form.title.trim() && form.content.trim());
```

Run: `npm.cmd test`

Expected: PASS。

- [ ] **Step 4: 改造管理页数据和操作状态**

使用 `listAnnouncements({ includeUnpublished: true })`；增加 `saving`、`deletingId`、`loadError`。保存前检查 `canSaveAnnouncement(form)`，请求期间禁用保存和当前删除按钮，成功后显示 `message.success`，失败时不清空表单。

删除改用 `useDialog()`：

```typescript
dialog.warning({
  title: '删除公告',
  content: `确定删除「${item.title}」吗？此操作不可撤销。`,
  positiveText: '删除',
  negativeText: '取消',
  onPositiveClick: () => performDelete(item),
});
```

- [ ] **Step 5: 复用正式 Markdown 渲染组件**

删除独立 `MarkdownIt` 和 `v-html`。增加：

```typescript
const previewContent = computed(() => ({
  title: form.value.title.trim() || '未命名公告',
  content: form.value.content,
}));
```

右侧使用 `<MarkdownComponent :content="previewContent" :show-nav="false" :show-heading-links="false" />`。编辑器容器使用 `grid grid-cols-1 gap-4 lg:grid-cols-2`，两侧设置稳定的 `min-h` 和桌面最大高度滚动，避免内容改变引发布局位移。

- [ ] **Step 6: 运行全部前端验证**

Run: `npm.cmd test`

Run: `node --max-old-space-size=4096 .\node_modules\vue-tsc\bin\vue-tsc.js -b`

Run: `npm.cmd run build`

Expected: 全部退出码为 `0`。

- [ ] **Step 7: 提交管理编辑器**

```bash
git add webapp/letapp/src/pages/admin/Announcements.vue webapp/letapp/src/utils/announcement-access.ts webapp/letapp/tests/announcement-access.test.ts
git commit -m "feat: complete announcement markdown editor"
```

### Task 7: 集成验证与浏览器验收

**Files:**
- Verify only; do not modify unrelated files.

**Interfaces:**
- Consumes: Tasks 1-6 的完整功能。
- Produces: 可复核的自动化和浏览器验收证据。

- [ ] **Step 1: 运行后端完整测试和语法检查**

Run: `D:\probject\oj\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Run: `D:\probject\oj\.venv\Scripts\python.exe -m py_compile controllers\auth_controller.py controllers\announcement_controller.py services\oidc_service.py services\user_service.py services\jwt_service.py models\auth_models.py utils\identity_utils.py`

Expected: 全部测试 PASS，语法检查退出码 `0`。

- [ ] **Step 2: 运行前端完整验证**

Run: `npm.cmd test`

Run: `npm.cmd run build`

Expected: 单元测试全部 PASS，生产构建退出码 `0`。

- [ ] **Step 3: 启动开发服务并进行浏览器验收**

Run: `npm.cmd run dev -- --host 127.0.0.1`

使用浏览器分别在 `1440x900` 和 `390x844` 检查：公开列表仅有已发布公告；manager 可见管理入口；管理编辑器桌面双栏、移动上下排列；Markdown 标题、代码块和容器预览与正式详情一致；保存失败保留内容；删除确认正常；页面无重叠和横向溢出。

- [ ] **Step 4: 检查最终差异和用户已有改动**

Run: `git status --short`

Run: `git diff --check`

Expected: 只包含本计划文件和实现文件；`webapp/letapp/public/learn/c-language/chapters/04-selection-structure.md` 的用户改动仍原样保留；`git diff --check` 无输出。

- [ ] **Step 5: 记录验证结果**

在最终交付中列出实际运行命令、通过数量、构建结果、浏览器视口和任何因环境无法执行的验证。不得用预期结果替代实际证据。
