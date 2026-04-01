"""
Shared pytest fixtures for async HTTP tests against the ASGI app.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import backend.core.config as config_module
from backend.main import app


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """
    Avoid cross-test pollution from cached pydantic-settings instances.
    """

    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """
    Async HTTP client wired to the FastAPI app in-process (no live server).
    """

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
