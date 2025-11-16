# FastAPI-Squillo Coding Standards

## General Principles

**SOLID Principles**
- Single Responsibility: Each class/module has one well-defined purpose
- Open/Closed: Open for extension, closed for modification
- Interface Segregation: Many specific interfaces over one general-purpose

**Other Core Principles**
- DRY (Don't Repeat Yourself): Single source of truth for each piece of logic
- KISS (Keep It Simple): Favor simplicity over complexity
- YAGNI (You Aren't Gonna Need It): Don't add features until needed
- Separation of Concerns: Separate different aspects into distinct sections

## Python Standards

**Imports**
- **NEVER use relative imports** - always use absolute imports from `src`
- Good: `from src.recipe_import_service.schemas.tiktok_schema import TikTokImportRequest`
- Bad: `from .schemas.tiktok_schema import TikTokImportRequest`
- Bad: `from ..services.tiktok_service import TiktokImportService`
- This ensures clarity and prevents import errors when modules are moved

**PEP 8 Naming**
- Modules/packages: `my_module.py`
- Classes: `UserService`, `PostRepository`
- Functions/variables: `get_user_by_email`, `user_count`
- Constants: `MAX_CONNECTIONS`, `API_TIMEOUT`
- Private: `_internal_var`, `__name_mangled`

**Formatting**
- Max 79 characters per line (99 acceptable)
- 2 blank lines around top-level functions/classes
- 1 blank line between methods

**Type Hints**
- Always use type hints for function parameters and return values
- Use native collections for Python 3.9+ (`list[str]`, `dict[str, int]`)
- Use `Optional[T]` for nullable values
- Use `Union` or `|` for multiple types
- Create type aliases for complex types

**Async/Await**
- Always await coroutines
- Use async-compatible libraries (`httpx`, `aiohttp`, `asyncpg`, `aiofiles`)
- Use `asyncio.gather()` for concurrent execution
- Never use blocking operations (`time.sleep`, sync `requests`)
- Always close connections with async context managers

**HTTP Requests**
- **ALWAYS add timeout to HTTP requests (default to 30 seconds)**
- Good: `httpx.get(url, timeout=30.0)`
- Good: `async with httpx.AsyncClient(timeout=30.0) as client:`
- Bad: `httpx.get(url)` (no timeout - can hang indefinitely)
- Use custom timeouts for specific endpoints if needed (e.g., `timeout=60.0` for slow APIs)

**Dependency Management**
- **ALWAYS use `poetry add <package>` to add dependencies**
- **NEVER manually modify pyproject.toml or poetry.lock**
- Use `poetry add --group dev <package>` for development dependencies
- Use `poetry add --group test <package>` for test dependencies
- Let Poetry handle version resolution and lock file updates

## Project Structure

**Domain-Driven Architecture**
```
src/
├── main.py                 # Application entry point
├── config.py               # Configuration
├── database/               # Database utilities
│   ├── session.py
│   └── base.py
├── auth/                   # Authentication domain
│   ├── router.py           # API routes
│   ├── schemas.py          # Pydantic models
│   ├── models.py           # Database models
│   ├── service.py          # Business logic
│   ├── repository.py       # Data access
│   ├── dependencies.py     # Dependencies
│   └── exceptions.py       # Custom exceptions
├── users/                  # Users domain
│   └── ...
└── posts/                  # Posts domain
    └── ...
```

**Why Domain-Driven**
- Clear boundaries between business domains
- Easy to scale and maintain
- Teams can work independently
- Promotes separation of concerns

## FastAPI Patterns

**Dependency Injection**
- Use `Annotated` for type-safe dependencies
- Create reusable type aliases (`DbSession`, `CurrentUser`)
- Chain dependencies for authorization
- Apply common dependencies at router level

**Router Organization**
- One router per domain/resource
- Use RESTful principles (GET, POST, PUT, DELETE)
- Plural nouns for resources (`/users`, not `/user`)
- Path parameters for IDs, query parameters for filters
- Proper HTTP status codes (200, 201, 204, 400, 404, 500)

**Pydantic Models**
- Separate schemas for create, update, and response
- Create custom base model with shared config
- Use validators for complex validation
- Update schemas have optional fields
- Response schemas exclude sensitive data
- Use `EmailStr`, `HttpUrl`, built-in validators

**Error Handling**
- Create custom exception hierarchy
- Register exception handlers globally
- Use specific exception types
- Include meaningful error messages
- Customize validation error responses

**Logging and Exception Strategy**
- **API/Router layer**: Use `logger.error()` with `exc_info=True` to log full stack traces
  - Good: `logger.error("Recipe import failed", exc_info=True)`
  - Always import logging and create logger: `logger = logging.getLogger(__name__)`
  - Log before raising HTTPException to capture full context
- **Service/Repository/Util layers**: Just raise exceptions with relevant error messages
  - Good: `raise ValueError("Invalid recipe URL format")`
  - Good: `raise HTTPException(status_code=404, detail="Recipe not found")`
  - Bad: Don't log in service/util layers - let API layer handle logging
  - Focus on clear, descriptive exception messages that help debugging
- **Layer Separation**: API logs + handles, Services raise + describe

**Middleware**
- CORS must be first in middleware stack
- One purpose per middleware
- Proper ordering: CORS → Logging → Auth → Rate Limiting

## Database Patterns

**Repository Pattern**
- Separate data access from business logic
- One repository per model
- Methods: `get`, `get_multi`, `create`, `update`, `delete`
- Use `selectinload` to avoid N+1 queries
- Keep repositories focused on data operations

**Service Layer**
- Contains business logic and validation
- Orchestrates repository calls
- Handles transactions
- Validates business rules
- Returns Pydantic schemas, not ORM models

**Layer Separation**
- Router → Service → Repository → Database
- Router handles HTTP concerns
- Service handles business logic
- Repository handles data access
- Never skip layers

## Testing

**Test Structure**
- Use pytest with async support
- Separate test database
- Fixtures for common setup
- One test file per module

**Test Types**
- Unit tests for service layer
- Integration tests for API endpoints
- Test error conditions
- Test validation rules
- Test authentication/authorization

**Coverage**
- Aim for 80%+ code coverage
- Focus on critical business logic
- Test happy paths and error cases

## Security

**Authentication & Authorization**
- Use bcrypt for password hashing
- Implement JWT with expiration
- Use dependency injection for auth checks
- Implement RBAC (role-based access control)

**Input Validation**
- Always validate with Pydantic
- Sanitize HTML content
- Use parameterized queries
- Validate file uploads

**Configuration**
- CORS: specific origins only in production
- Rate limiting on public endpoints
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- HTTPS only in production
- Environment variables for secrets

## Documentation

**Code Documentation**
- Docstrings for all public functions/classes/modules
- Document parameters, return values, exceptions
- Keep docstrings updated with code changes

**API Documentation**
- Specify `response_model` for all endpoints
- Use `summary` and `description` parameters
- Document all possible status codes
- Use tags to organize endpoints
- Mark deprecated endpoints with `deprecated=True`

**Versioning**
- Use URL path versioning (`/api/v1`, `/api/v2`)
- Maintain separate docs per version
- Document breaking changes
- Provide migration guides

## Code Quality Checklist

- [ ] Follows SOLID principles
- [ ] Type hints on all functions
- [ ] Proper async/await usage
- [ ] Domain-driven structure
- [ ] Repository pattern for data access
- [ ] Service layer for business logic
- [ ] Pydantic validation on all inputs
- [ ] Custom exception handling
- [ ] Comprehensive tests
- [ ] Security best practices
- [ ] Complete documentation
- [ ] No secrets in code
- [ ] Proper error messages

## Linting

**IMPORTANT: Always run `make lint` after making code changes**
- Run `make lint` before committing any changes
- Fix all linting errors and warnings
- This ensures code quality and consistency across the project

**Remember: Code is read more often than written. Prioritize clarity, modularity, and maintainability.**
