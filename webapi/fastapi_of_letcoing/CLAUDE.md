# CLAUDE.md

**请使用中文回答和中文解释**

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Flask-based code execution API service** (LetCoding API) that allows users to execute code in 30+ programming languages via the Glot.io API. The project features a sophisticated dependency injection architecture, JWT authentication with OAuth support (GitHub, custom OIDC), Redis caching, and PostgreSQL database integration using Peewee ORM.

**Key Technologies:**
- Flask 3.1.2 + Flask-RESTX for API documentation
- aiohttp for async HTTP requests
- PostgreSQL with Peewee ORM
- Redis for caching and session management
- JWT + OAuth (GitHub, OIDC)
- Custom dependency injection container

## Essential Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 6173)
python main.py

# API documentation available at:
# http://localhost:6173/swagger/
```

### Database Operations

```bash
# Initialize database tables
# Tables are created automatically on first run via Peewee ORM
# Models defined in models/db_models.py

# Test database connection (in Python)
from services.database_service import DatabaseService
from core.di_container import inject
db = inject(DatabaseService)
db.test_connection()
```

### Redis Operations

```bash
# Test Redis connection
redis-cli ping

# Monitor Redis operations
redis-cli monitor

# Clear Redis cache (use with caution)
redis-cli FLUSHDB
```

### Testing

```bash
# Currently no formal test suite
# Manual API testing:
curl http://localhost:6173/auth/providers
curl -X POST http://localhost:6173/code/run/public \
  -H "Content-Type: application/json" \
  -d '{"code": "console.log(\"Hello\")", "language": "javascript"}'
```

## Architecture Overview

### Layered Architecture

This project follows a strict layered architecture with dependency injection:

```
Request Flow:
HTTP Request → Middleware (auth) → Controller → Service Layer → External APIs/Database/Redis

Layer Responsibilities:
- Controllers (controllers/): HTTP routing, request validation, response formatting
- Services (services/): Business logic, external API calls, data processing
- Middleware (middleware/): Authentication, rate limiting
- Models (models/): Data structures (dataclasses for API models, Peewee for DB models)
- Core (core/): DI container, service configuration, database configuration
- Interfaces (interfaces/): Abstract service interfaces (ABC)
```

### Dependency Injection System

**The project uses a custom DI container** (`core/di_container.py`) with three lifecycles:

1. **Singleton**: One instance per application (ConfigService, LoggerService, RedisService, DatabaseService)
2. **Scoped**: One instance per request (GlotService)
3. **Transient**: New instance every time (rarely used)

**How to use DI:**

```python
# Method 1: Constructor injection (preferred for services)
from interfaces.service_interfaces import IConfigService, ILoggerService
from core.di_container import Injectable

class MyService(Injectable):
    def __init__(self, config: IConfigService, logger: ILoggerService):
        self._config = config
        self._logger = logger

# Method 2: Runtime injection (for controllers, one-off usage)
from core.di_container import inject
from services.user_service import UserService

def my_function():
    user_service = inject(UserService)
    return user_service.get_user_by_id(123)
```

**Service Registration** happens in `core/service_config.py`:

```python
def service_configurator(container):
    container.register_singleton(IConfigService, factory=lambda: ConfigService(app_config))
    container.register_singleton(IRedisService, RedisService)
    container.register_scoped(ICodeExecutionService, GlotService)
```

### Database Architecture

The project uses **modular database services** built on Peewee ORM:

- **Base Service**: `DatabaseService` provides generic CRUD operations
- **Specialized Services**: `UserService`, `CodeExecutionService`, `APIService` inherit from `DatabaseService`
- **Models**: Defined in `models/db_models.py`, all inherit from `BaseModel`

**Key database services:**
- `DatabaseService`: Generic CRUD, connection management
- `UserService`: User-specific operations (create_user, get_user_by_username, etc.)
- `UserService` and similar services inherit both `DatabaseService` and `Injectable`

**Database configuration** is managed through environment variables (see main.py:26-33):
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- DB_MAX_CONNECTIONS, DB_STALE_TIMEOUT

### Service Layer Patterns

**Key Services and Their Purposes:**

1. **ConfigService** (`services/config_service.py`): Centralized configuration management from environment variables
2. **GlotService** (`services/glot_service.py`): Async code execution via Glot.io API
3. **OIDCService** (`services/oidc_service.py`): OAuth/OIDC authentication (GitHub, custom providers)
4. **JWTService** (`services/jwt_service.py`): JWT token generation, verification, refresh
5. **RedisService** (`services/redis_service.py`): Caching, session management, rate limiting
6. **DatabaseService** (`services/database_service.py`): Base database operations with Peewee
7. **UserService** (`services/user_service.py`): User management (create, query, update users)
8. **LoggerService** (`services/logger_service.py`): Structured logging

### Authentication System

The project implements **multi-provider OAuth + JWT**:

1. **OIDC Flow**: User initiates login → redirected to OAuth provider → callback handles token exchange → JWT tokens issued
2. **JWT Tokens**: Access token (short-lived, default 1h) + Refresh token (long-lived, default 7d)
3. **Middleware**: `AuthMiddleware` provides decorators:
   - `@AuthMiddleware.require_auth`: Protected endpoints
   - `@AuthMiddleware.optional_auth`: Guest/authenticated access
   - `@AuthMiddleware.rate_limit(max_requests, window_seconds)`: Rate limiting
4. **Token Management**: Redis stores token blacklist, refresh tokens, user sessions

**Supported OAuth Providers:**
- GitHub OAuth (via GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)
- Custom OIDC providers (via OIDC_PROVIDERS JSON env var)

### Redis Usage Patterns

Redis is used for:
1. **JWT Token Blacklist**: Revoked tokens stored with TTL matching token expiry
2. **Rate Limiting**: Counter keys like `rate_limit:{user_id}:{endpoint}` with TTL
3. **Code Execution Cache**: Cache results for identical code+language combinations
4. **User Session Data**: Temporary user information with TTL

**Key naming conventions:**
- `user:profile:{user_id}` - User profile cache
- `session:{session_id}` - User session data
- `rate_limit:api:{user_id}:{endpoint}` - Rate limit counters
- `blacklist:token:{jti}` - Revoked JWT tokens

## Critical Implementation Details

### Adding a New Service

Complete workflow (follow this order):

1. **Define interface** in `interfaces/service_interfaces.py`:
```python
class IMyService(ABC):
    @abstractmethod
    def my_method(self) -> str:
        pass
```

2. **Implement service** in `services/my_service.py`:
```python
from interfaces.service_interfaces import IMyService, IConfigService
from core.di_container import Injectable

class MyService(IMyService, Injectable):
    def __init__(self, config: IConfigService):
        self._config = config

    def my_method(self) -> str:
        return "result"
```

3. **Register service** in `core/service_config.py`:
```python
def service_configurator(container):
    # ... existing registrations ...
    container.register_singleton(IMyService, MyService)
```

4. **Create controller** in `controllers/my_controller.py`:
```python
from flask_restx import Namespace, Resource
from core.di_container import inject

api = Namespace('my_module', description='My module')

@api.route('/action')
class MyController(Resource):
    def get(self):
        service = inject(IMyService)
        return {'result': service.my_method()}
```

5. **Register namespace** in `main.py`:
```python
from controllers.my_controller import api as my_api
api.add_namespace(my_api, path='/my-module')
```

### Database Service Pattern

When creating a new database-backed service:

1. **Define model** in `models/db_models.py`:
```python
class MyModel(BaseModel):
    name = CharField(max_length=100, unique=True)
    value = TextField()

    class Meta:
        table_name = "my_table"
```

2. **Create service** inheriting from `DatabaseService`:
```python
from services.database_service import DatabaseService
from core.di_container import Injectable

class MyTableService(DatabaseService, Injectable):
    async def create_record(self, name: str, value: str) -> Dict[str, Any]:
        return await self.create(MyModel, name=name, value=value)

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            record = MyModel.get(MyModel.name == name)
            return record.to_dict()
        except DoesNotExist:
            return None
```

3. **Register in service config** with factory function:
```python
def service_configurator(container):
    def create_my_table_service():
        config = container.resolve(IConfigService)
        return MyTableService(config)

    container.register_singleton(MyTableService, factory=create_my_table_service)
```

### Working with Async Code

The project mixes **sync Flask with async services**:

- Flask routes are sync, but services use `async/await`
- Use `asyncio.run()` or `asyncio.create_task()` to call async services from sync controllers
- GlotService uses `aiohttp` for async HTTP requests
- All database operations are async (though Peewee itself is sync, the service layer wraps them)

Example:
```python
import asyncio

@api.route('/execute')
class ExecuteController(Resource):
    def post(self):
        service = inject(ICodeExecutionService)
        # Call async method from sync controller
        result = asyncio.run(service.execute_code(request.get_json()))
        return result
```

### Environment Configuration

**Critical environment variables** (see main.py and README.md for complete list):

**Required:**
- `API_TOKEN`: Glot.io API token (required for code execution)

**JWT (recommended for production):**
- `JWT_SECRET_KEY`: Strong secret for JWT signing
- `JWT_ACCESS_TOKEN_EXPIRE`: Access token TTL in seconds (default: 3600)
- `JWT_REFRESH_TOKEN_EXPIRE`: Refresh token TTL in seconds (default: 604800)

**Redis (recommended for production):**
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `REDIS_TIMEOUT`

**Database (required if using DB features):**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DB_MAX_CONNECTIONS`, `DB_STALE_TIMEOUT`

**OAuth (optional):**
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- `OIDC_PROVIDERS` (JSON string for custom providers)

Configuration loading priority: Environment variables → `.env` file → defaults in main.py

## Code Style and Conventions

### Naming Conventions

- **Interfaces**: `IServiceName` (e.g., `IConfigService`)
- **Implementations**: `ServiceName` (e.g., `ConfigService`)
- **Controllers**: `ResourceNameController` (e.g., `CodeExecutionController`)
- **Models**: PascalCase for classes, snake_case for table names
- **Service methods**: snake_case, descriptive verbs (get_user, create_record, execute_code)

### File Organization

- One service per file in `services/`
- One controller namespace per file in `controllers/`
- All interface definitions in `interfaces/service_interfaces.py`
- Database models in `models/db_models.py`
- API data models (dataclasses) in `models/` (e.g., `glot_models.py`, `auth_models.py`)

### Error Handling Pattern

Follow this pattern in services:
```python
try:
    result = await self._perform_operation()
    self._logger.info(f"Operation successful: {result}")
    return result
except SpecificException as e:
    self._logger.error(f"Specific error: {e}")
    raise ValueError(f"Business-friendly message: {e}")
except Exception as e:
    self._logger.error(f"Unexpected error: {e}")
    raise RuntimeError(f"Internal error: {e}")
```

Controllers should catch service exceptions and return appropriate HTTP status codes:
```python
try:
    result = service.my_method()
    return {'data': result}, 200
except ValueError as e:
    return {'error': str(e)}, 400
except RuntimeError as e:
    return {'error': 'Internal server error'}, 500
```

### Dataclass Models

Use `@dataclass` for API models with `to_dict()` methods:
```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class MyModel:
    name: str
    value: Optional[str] = None
    items: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'items': self.items
        }
```

## Common Pitfalls and Solutions

### Pitfall 1: Circular Dependencies

**Problem**: Service A depends on Service B, which depends on Service A.

**Solution**:
- Redesign services to eliminate circular dependency
- Use event-driven pattern instead of direct service calls
- Extract common functionality into a third service

### Pitfall 2: Forgetting to Register Services

**Problem**: `ValueError: 服务 {service_type} 未注册`

**Solution**: Always register new services in `core/service_config.py` before using them.

### Pitfall 3: Redis Connection Failures

**Problem**: Redis operations fail silently or with connection errors.

**Solution**:
- Use `redis_service.is_connected()` to check connection
- Implement graceful degradation (continue without cache if Redis is down)
- Use `redis_service.reconnect()` to attempt reconnection

### Pitfall 4: Async/Sync Mixing Issues

**Problem**: Calling async functions without `await` or `asyncio.run()`.

**Solution**:
- In async contexts: Use `await service.async_method()`
- In sync contexts (controllers): Use `asyncio.run(service.async_method())`
- Mark service methods with `async def` if they perform I/O operations

### Pitfall 5: Database Model Changes

**Problem**: Schema changes not reflected in database.

**Solution**:
- Peewee doesn't auto-migrate; modify database schema manually or recreate tables
- For development: Delete tables and recreate with `create_tables()` in models/db_models.py
- For production: Use migration tools or write migration scripts

### Pitfall 6: Missing BaseModel.to_dict() for Sensitive Data

**Problem**: Password hashes or secrets exposed in API responses.

**Solution**: Override `to_dict()` in models to exclude sensitive fields:
```python
class User(BaseModel):
    password_hash = CharField(max_length=255)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.pop('password_hash', None)  # Remove sensitive field
        return data
```

## Working with This Codebase

### When modifying authentication

- JWT token logic is in `services/jwt_service.py`
- OAuth flow logic is in `services/oidc_service.py`
- Middleware decorators are in `middleware/auth_middleware.py`
- Token blacklist and refresh tokens are stored in Redis
- Test token generation/verification independently before integration

### When adding API endpoints

1. Create or extend namespace in `controllers/`
2. Use Flask-RESTX models for request/response documentation
3. Apply `@AuthMiddleware.require_auth` if authentication is needed
4. Use dependency injection to access services
5. Return JSON with appropriate HTTP status codes
6. Register namespace in `main.py` with URL prefix

### When working with Redis

- Always check connection with `is_connected()` before critical operations
- Use meaningful key naming with namespaces (e.g., `user:profile:{id}`)
- Set appropriate TTL for all cached data
- Implement cache invalidation strategy for updated data
- Use Redis CLI for debugging: `redis-cli --scan --pattern "user:*"`

### When working with the database

- Define models in `models/db_models.py` inheriting from `BaseModel`
- Create specialized service classes inheriting from `DatabaseService`
- Use async wrappers for database operations
- Test connection with `database_service.test_connection()`
- Use `to_dict()` to convert models to API responses
- Add indexes to frequently queried fields

## Language Support

The service supports 30+ languages via Glot.io. Language mappings are in `services/glot_service.py` in the `LANGUAGES` dictionary. When adding support for new languages, update this dictionary and verify the language is supported by Glot.io API.

## Troubleshooting

**Issue: "服务 {type} 未注册"**
→ Register the service in `core/service_config.py`

**Issue: Redis connection errors**
→ Check Redis is running (`redis-cli ping`), verify REDIS_* env vars, check `redis_service.is_connected()`

**Issue: Database connection errors**
→ Verify PostgreSQL is running, check DB_* env vars, test with `database_service.test_connection()`

**Issue: "API_TOKEN 未配置"**
→ Set API_TOKEN environment variable or in .env file

**Issue: OAuth callback fails**
→ Verify OAuth provider config, check redirect_uri matches provider settings, inspect logs from `oidc_service`

**Issue: JWT tokens not working**
→ Check JWT_SECRET_KEY is set and consistent, verify token expiry times, check Redis connection for blacklist

## Additional Resources

- Flask-RESTX documentation: For API documentation features
- Peewee ORM documentation: For database model operations
- Glot.io API documentation: For supported languages and execution limits
- OAuth 2.0 / OIDC specs: For understanding authentication flows

## Key Files to Understand the Architecture

Reading these files in order will give you a complete understanding:

1. `main.py` - Application entry point, configuration, namespace registration
2. `core/di_container.py` - Dependency injection container implementation
3. `core/service_config.py` - Service registration configuration
4. `interfaces/service_interfaces.py` - All service interfaces
5. `services/config_service.py` - Configuration management pattern
6. `services/glot_service.py` - Async service pattern, external API integration
7. `services/database_service.py` - Database service base class with CRUD operations
8. `services/user_service.py` - Example of specialized database service
9. `middleware/auth_middleware.py` - Authentication and authorization decorators
10. `controllers/code_controller.py` - Controller pattern, dependency injection in action
