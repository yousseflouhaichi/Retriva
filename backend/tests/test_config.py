"""
Settings validation for ingestion timeouts and related derived values.
"""

from __future__ import annotations

import pytest

import backend.core.config as config_module
from backend.core.config import Settings


def test_effective_ingestion_job_timeout_defaults_above_unstructured(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Default ARQ job limit must exceed the Unstructured httpx timeout so the worker is not cut off first.
    """

    monkeypatch.setenv("UNSTRUCTURED_TIMEOUT_SECONDS", "120")
    monkeypatch.delenv("INGESTION_JOB_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("INGESTION_JOB_TIMEOUT_BUFFER_SECONDS", raising=False)
    config_module.get_settings.cache_clear()
    try:
        settings = Settings()
        assert settings.effective_ingestion_job_timeout_seconds() > settings.unstructured_timeout_seconds
    finally:
        config_module.get_settings.cache_clear()


def test_effective_ingestion_job_timeout_uses_explicit_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    INGESTION_JOB_TIMEOUT_SECONDS wins when set and must still exceed UNSTRUCTURED_TIMEOUT_SECONDS.
    """

    monkeypatch.setenv("UNSTRUCTURED_TIMEOUT_SECONDS", "100")
    monkeypatch.setenv("INGESTION_JOB_TIMEOUT_SECONDS", "250")
    monkeypatch.delenv("INGESTION_JOB_TIMEOUT_BUFFER_SECONDS", raising=False)
    config_module.get_settings.cache_clear()
    try:
        settings = Settings()
        assert settings.effective_ingestion_job_timeout_seconds() == 250.0
    finally:
        config_module.get_settings.cache_clear()


def test_rejects_job_timeout_not_above_unstructured(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Misconfiguration where ARQ limit does not exceed parse timeout fails at startup.
    """

    monkeypatch.setenv("UNSTRUCTURED_TIMEOUT_SECONDS", "300")
    monkeypatch.setenv("INGESTION_JOB_TIMEOUT_SECONDS", "300")
    config_module.get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="Effective ingestion job timeout"):
            Settings()
    finally:
        config_module.get_settings.cache_clear()
        for key in ("UNSTRUCTURED_TIMEOUT_SECONDS", "INGESTION_JOB_TIMEOUT_SECONDS"):
            monkeypatch.delenv(key, raising=False)
