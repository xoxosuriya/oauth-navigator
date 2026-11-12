import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ConnectionStartRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Stable opaque identifier for the browser session",
    )
    alias: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional human-friendly connection alias",
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="Frontend URL to redirect the user back to after OAuth flow",
    )
    force_new: Optional[bool] = Field(
        default=False,
        description="Force creating a new connection link even if an ACTIVE connection already exists",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-\.]{3,64}$", clean):
            raise ValueError(
                "user_id must be 3-64 characters and contain only alphanumeric, dash, underscore, or period."
            )
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
