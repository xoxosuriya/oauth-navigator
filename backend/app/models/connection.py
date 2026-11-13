import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ConnectionStartRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Optional client session identifier; if provided, must match authenticated session",
    )
    alias: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional human-friendly connection alias",
    )
    callback_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Frontend URL to redirect the user back to after OAuth flow",
    )
    force_new: Optional[bool] = Field(
        default=False,
        description="Force creating a new connection link even if an ACTIVE connection already exists",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-\.]{3,64}$", clean):
            raise ValueError(
                "user_id must be 3-64 characters and contain only alphanumeric, dash, underscore, or period."
            )
        return clean

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        lowered = clean.lower()
        if not (lowered.startswith("http://") or lowered.startswith("https://")):
            raise ValueError("callback_url must use an http or https protocol scheme.")
        if any(bad in lowered for bad in ("javascript:", "data:", "vbscript:", "\n", "\r")):
            raise ValueError("Invalid characters or dangerous scheme in callback_url.")
        return clean


class ConnectionStartResponse(BaseModel):
    redirect_url: Optional[str] = Field(default=None, description="Composio Connect authorization link")
    connected_account_id: str = Field(..., description="Unique Composio connected account identifier")
    expires_at: Optional[str] = Field(default=None, description="ISO timestamp when the link expires")
    toolkit_slug: str = Field(..., description="Toolkit slug being connected")
    is_custom_auth: bool = Field(default=False, description="Whether connection uses custom app credentials")
    status: str = Field(default="INITIATED", description="Lifecycle status: INITIATED or ACTIVE")
    already_active: bool = Field(default=False, description="Whether an existing ACTIVE connection was returned")
    alias: Optional[str] = Field(default=None, description="Resolved alias for this connection")
    message: Optional[str] = Field(default=None, description="Helpful status or next steps message")


class ConnectedAccountResponse(BaseModel):
    id: str = Field(..., description="Unique Composio connected account identifier")
    toolkit_slug: str = Field(..., description="Toolkit slug")
    status: str = Field(..., description="Connection lifecycle status (INITIALIZING, INITIATED, ACTIVE, FAILED, EXPIRED, CANCELLED)")
    status_reason: Optional[str] = Field(default=None, description="Detailed explanation if failed or pending")
    created_at: Optional[str] = Field(default=None, description="ISO creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="ISO update timestamp")
    user_id: str = Field(..., description="Owner user ID")
    alias: Optional[str] = Field(default=None, description="Connection alias")


class ConnectedAccountListResponse(BaseModel):
    items: List[ConnectedAccountResponse] = Field(default_factory=list)
    total_items: int = Field(default=0)


class ShopifyConfigStatusResponse(BaseModel):
    has_custom_config: bool
    auth_config_id: Optional[str] = None
    setup_instructions: str
