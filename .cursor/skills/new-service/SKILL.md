# Skill: Create a new service

Use this when adding a new service file to backend/services/.

## Steps
1. Create backend/services/{name}.py
2. Add module docstring explaining what the service does and why
3. Import settings: from core.config import get_settings
4. All functions must be async
5. Every function needs a type-annotated signature and a docstring
6. Handle exceptions inside the service, never let raw errors bubble up
7. If new config values are needed, add them to core/config.py first
8. If new request/response types are needed, add them to models/schemas.py first
9. Wire the service into the relevant router via dependency injection

## Template
```python
"""
Module docstring: what this service does and why it exists.
"""
from core.config import get_settings
from models.schemas import ExampleSchema

settings = get_settings()


async def example_function(param: str) -> ExampleSchema:
    """
    What this function does.
    Args:
        param: what this parameter is
    Returns:
        ExampleSchema: what is returned and why
    """
    try:
        # implementation
        pass
    except Exception as exc:
        raise RuntimeError(f"example_function failed for param={param}: {exc}") from exc
```