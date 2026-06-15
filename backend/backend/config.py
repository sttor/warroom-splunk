"""
WarRoom Configuration Management
================================
Loads configuration from environment variables / .env file using pydantic BaseSettings.
Supports Splunk, LLM provider, and application settings with validation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


# Resolve .env path relative to this file's directory (backend/) or project root
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_ENV_FILE = _PROJECT_ROOT / ".env" if (_PROJECT_ROOT / ".env").exists() else _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Central configuration for the WarRoom backend.
    Values are loaded from environment variables and/or a .env file.
    """

    # ── Splunk Connection ──────────────────────────────────────────────
    splunk_host: str = Field(default="localhost", description="Splunk management host")
    splunk_port: int = Field(default=8089, description="Splunk management port")
    splunk_token: str = Field(default="", description="Splunk authentication token (Bearer)")
    splunk_scheme: Literal["http", "https"] = Field(default="https", description="HTTP scheme for Splunk REST API")
    splunk_verify_ssl: bool = Field(default=False, description="Verify SSL certs for Splunk REST API")

    # ── Splunk MCP Server ──────────────────────────────────────────────
    splunk_mcp_server_path: str = Field(
        default="",
        description="Filesystem path to the Splunk MCP server script (splunk_mcp.py)",
    )

    # ── LLM Provider ──────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic", "google"] = Field(
        default="openai",
        description="Which LLM provider to use",
    )
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    google_api_key: str = Field(default="", description="Google Generative AI API key")
    llm_model: str = Field(default="", description="Override the default model for the selected provider")

    # ── Application ───────────────────────────────────────────────────
    app_host: str = Field(default="0.0.0.0", description="FastAPI bind host")
    app_port: int = Field(default=8000, description="FastAPI bind port")
    demo_mode: bool = Field(default=True, description="Run with synthetic demo data (no live Splunk needed)")

    # ── Pydantic-settings configuration ───────────────────────────────
    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,          # Env vars are matched case-insensitively
        "extra": "ignore",                # Ignore unexpected env vars
    }

    # ── Derived helpers ───────────────────────────────────────────────

    @property
    def active_api_key(self) -> str:
        """Return the API key for the currently selected LLM provider."""
        mapping = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }
        return mapping.get(self.llm_provider, "")

    @property
    def resolved_model(self) -> str:
        """Return the model name, falling back to a sensible per-provider default."""
        if self.llm_model:
            return self.llm_model
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-20250514",
            "google": "gemini-2.0-flash",
        }
        return defaults[self.llm_provider]

    @field_validator("splunk_port", "app_port", mode="before")
    @classmethod
    def _coerce_port(cls, v: object) -> int:
        return int(v)

    @field_validator("demo_mode", "splunk_verify_ssl", mode="before")
    @classmethod
    def _coerce_bool(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes")
        return bool(v)


# Module-level singleton – import this everywhere
settings = Settings()
