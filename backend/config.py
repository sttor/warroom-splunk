import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

_ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    slack_bot_token: Optional[str] = Field(default=None)
    slack_app_token: Optional[str] = Field(default=None)
    
    # Splunk MCP Connection
    splunk_mcp_url: str = Field(default="https://prd-p-13hjb.splunkcloud.com:8089/services/mcp")
    splunk_mcp_token: Optional[str] = Field(default=None)
    splunk_hosted_key: Optional[str] = Field(default=None)
    
    # VirusTotal Integration
    vt_api_key: Optional[str] = Field(default=None)
    
    # Jira MCP Integration
    jira_mcp_url: Optional[str] = Field(default=None)
    jira_mcp_token: Optional[str] = Field(default=None)
    
    # Slack Integration
    slack_bot_token: Optional[str] = Field(default=None)
    slack_app_token: Optional[str] = Field(default=None)
    
    # LLM Settings
    ollama_model: str = Field(default="ollama/qwen3.5:4b-q4_K_M")
    llm_api_key: Optional[str] = Field(default=None) # For fallback to OpenAI/Azure
    llm_api_base: Optional[str] = Field(default=None) # For Azure or custom endpoints

    model_config = {
        "env_file": str(_ENV_FILE),
        "extra": "ignore",
    }

def save_settings(new_settings: dict):
    """Saves the configuration to the .env file."""
    lines = []
    if _ENV_FILE.exists():
        with open(_ENV_FILE, "r") as f:
            lines = f.readlines()
            
    # Update or add keys
    env_dict = {}
    for line in lines:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_dict[k] = v
            
    for k, v in new_settings.items():
        if v and v != "********": # Don't save placeholder passwords
            env_dict[k.upper()] = str(v)
            
    with open(_ENV_FILE, "w") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")
            
    # Force reload of settings in process
    for k, v in env_dict.items():
        os.environ[k] = v
        
    global settings
    new_s = Settings()
    for field in new_s.model_dump():
        setattr(settings, field, getattr(new_s, field))

settings = Settings()
