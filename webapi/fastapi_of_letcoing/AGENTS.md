# AGENTS.md

**请使用中文回答和中文解释**

This document provides guidelines for agentic coding agents working on this Flask-based code execution API service.

## Project Overview

This is a Flask web API service that provides code execution capabilities by integrating with the Glot.io API. The service supports 30+ programming languages and uses asynchronous HTTP requests for better performance.

**Architecture:**
- `main.py` - Flask application entry point with API routes
- `services/glot_service.py` - Core service for Glot.io API integration
- `controller/` - Directory for future controller implementations

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python3 main.py
```

The application runs on `http://localhost:5000` by default.

### Testing
This project currently does not have a formal test suite. When implementing tests:

```bash
# Run pytest (if added)
python3 -m pytest

# Run specific test file
python3 -m pytest tests/test_service.py

# Run with coverage
python3 -m pytest --cov=services
```

### Code Quality
```bash
# Check syntax
python3 -m py_compile main.py services/glot_service.py

# Format code (if black is added)
black main.py services/

# Lint (if flake8 is added)
flake8 main.py services/
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local imports
- Use absolute imports for local modules
- Keep imports sorted alphabetically within each section
```python
import asyncio
import os
from typing import Dict, List, Optional

import aiohttp
from flask import Flask, request, jsonify

from services.glot_service import GlotService
```

### Formatting and Naming
- **PEP 8 compliant** - Use 4 spaces for indentation
- **Line length**: Maximum 88-100 characters
- **Variable names**: `snake_case` for functions and variables
- **Class names**: `PascalCase` for classes
- **Constants**: `UPPER_SNAKE_CASE` for module-level constants
- **Private methods**: Prefix with underscore `_`

### Type Hints
- Use type hints for all function parameters and return values
- Import from `typing` module for complex types
- Use `Optional[T]` for nullable types

```python
async def run_glot_async(self, 
                        api_token: str, 
                        code: str, 
                        language: str = "javascript", 
                        stdin: Optional[str] = None) -> str:
```

### Data Models
- Use `@dataclass` for data structures
- Provide `to_dict()` methods for serialization
- Initialize list/dict defaults properly in `__post_init__`

```python
@dataclass
class PostDataModel:
    files: List[PostFile] = None
    stdin: Optional[str] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []
    
    def to_dict(self):
        return {
            "files": [f.to_dict() for f in self.files],
            "stdin": self.stdin
        }
```

### Error Handling
- Use try-except blocks for API calls and I/O operations
- Handle specific exceptions when possible
- Return meaningful error messages to users
- Log errors appropriately (logging not currently implemented)

```python
try:
    async with aiohttp.ClientSession(timeout=self.timeout) as session:
        async with session.post(url, json=data, headers=headers) as response:
            # Handle response
except asyncio.TimeoutError:
    return "请求超时"
except aiohttp.ClientError as ex:
    return f"请求出错: {str(ex)}"
except Exception as ex:
    return f"请求出错: {str(ex)}"
```

### API Endpoints
- Use Flask decorators for routing
- Validate input parameters
- Return JSON responses with appropriate HTTP status codes
- Handle missing required fields gracefully

```python
@app.route('/run', methods=['POST'])
async def post():
    # Validate input
    model = request.get_json()
    if not model:
        return jsonify({'error': '请求体不能为空'}), 400
    
    # Extract and validate parameters
    code = model.get('code', '')
    if not code or code.strip() == "":
        return jsonify({'error': '代码不能为空'}), 400
    
    # Process and return response
    result = await glot_service.run_glot_async(api_token, code, language, stdin)
    return jsonify(result), 200
```

### Security Considerations
- Escape output to prevent injection attacks
- Validate API tokens from environment variables
- Use HTTPS for external API calls
- Never log sensitive information like API tokens

```python
@staticmethod
def _escape(text: str) -> str:
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
```

## Configuration

### Environment Variables
- `API_TOKEN`: Required Glot.io API token
- Can be set via environment variable or Flask app config

### Constants
- Language mappings stored as class constant `LANGUAGES`
- Default timeout: 30 seconds for HTTP requests

## Patterns to Follow

### Async/Await
- Use async/await for all HTTP requests
- Properly handle async context managers with `async with`

### Service Layer Pattern
- Business logic separated from Flask routes
- Services should be reusable and testable
- Use dependency injection for service instances

### Data Transfer Objects
- Use dataclasses for request/response models
- Provide serialization methods
- Validate data at service boundaries

## Dependencies

Key dependencies and their purposes:
- `Flask`: Web framework
- `aiohttp`: Async HTTP client for Glot.io API calls
- `requests`: Alternative HTTP client (currently unused)
- `dataclasses`: Built-in data modeling (Python 3.7+)

## Common Tasks

### Adding New Language Support
1. Add language mapping to `LANGUAGES` dictionary in `GlotService`
2. Update documentation in README.md
3. Test the new language integration

### Adding New API Endpoints
1. Define route in `main.py` using `@app.route()`
2. Validate request data
3. Call appropriate service methods
4. Return JSON response with proper status code

### Modifying Service Logic
1. Update methods in `GlotService` class
2. Maintain async/await pattern
3. Update data models if needed
4. Test error scenarios

## Future Considerations

- Consider adding comprehensive test suite with pytest
- Implement proper logging instead of return strings
- Add API rate limiting
- Implement caching for repeated requests
- Consider using FastAPI instead of Flask for better async support