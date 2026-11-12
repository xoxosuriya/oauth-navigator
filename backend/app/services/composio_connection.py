import logging
from typing import Dict, Any, Optional, List
import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.connection import (
    ConnectionStartResponse,
    ConnectedAccountResponse,
    ConnectedAccountListResponse,
    ShopifyConfigStatusResponse,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLKITS = {"slack", "gmail", "shopify"}


class ComposioConnectionService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    def _get_headers(self) -> Dict[str, str]:
        key = settings.COMPOSIO_API_KEY.strip() if settings.COMPOSIO_API_KEY else ""
        if not key:
            raise HTTPException(
                status_code=503,
                detail="COMPOSIO_API_KEY is not configured on the backend. Connection services are unavailable.",
            )
        return {
            "x-api-key": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ComposioOAuthGuideBackend/1.0",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = self._get_headers()
        url = f"{settings.COMPOSIO_BASE_URL.rstrip('/')}{endpoint}"
        timeout = httpx.Timeout(15.0, connect=5.0)

        try:
            if self._client:
                res = await self._client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.request(
                        method=method,
                        url=url,
                        json=json_data,
                        params=params,
                        headers=headers,
                    )

            if res.status_code == 401 or res.status_code == 403:
                logger.error(f"[ComposioConnection] Auth error {res.status_code} at {endpoint}")
                raise HTTPException(
                    status_code=502,
                    detail="Composio API authentication failed. Verify the backend COMPOSIO_API_KEY.",
                )

            if res.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Composio API rate limit exceeded. Please wait a moment before retrying.",
                )

            if res.status_code == 404:
                try:
                    err_json = res.json()
                    msg = err_json.get("error", {}).get("message") or "Resource not found on upstream provider."
                except Exception:
                    msg = "Resource not found on upstream provider."
                raise HTTPException(status_code=404, detail=msg)

            if res.status_code >= 400:
                try:
                    err_json = res.json()
                    msg = err_json.get("error", {}).get("message") or f"Upstream request failed ({res.status_code})"
                except Exception:
                    msg = f"Upstream request failed ({res.status_code})"
                raise HTTPException(status_code=res.status_code, detail=msg)

            return res.json()

        except httpx.TimeoutException:
            logger.error(f"[ComposioConnection] Timeout contacting Composio at {endpoint}")
            raise HTTPException(
                status_code=504,
                detail="Connection to Composio upstream service timed out.",
            )
        except httpx.RequestError as exc:
            logger.error(f"[ComposioConnection] Network error contacting Composio: {exc}")
            raise HTTPException(
                status_code=502,
                detail="Network error communicating with Composio upstream service.",
            )

    async def get_or_create_auth_config(self, toolkit_slug: str) -> Dict[str, Any]:
        """
        Locates or initializes the appropriate Composio auth configuration.
        Distinguishes Composio-managed OAuth (Slack, Gmail) from Custom OAuth (Shopify).
        """
        slug = toolkit_slug.lower().strip()

        # 1. Special handling for Shopify
        if slug == "shopify":
            custom_id = settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID
            if custom_id:
                try:
                    config = await self._request("GET", f"/auth_configs/{custom_id}")
                    if config.get("toolkit", {}).get("slug") == "shopify":
                        return {
                            "id": custom_id,
                            "is_custom_auth": True,
                            "raw": config,
                        }
                except HTTPException:
                    logger.warning(f"Configured COMPOSIO_SHOPIFY_AUTH_CONFIG_ID '{custom_id}' invalid or not found.")

            raise HTTPException(
                status_code=400,
                detail=(
                    "Shopify does not provide Composio-managed credentials. "
                    "A Custom OAuth App is required. Please create a Shopify App in the Shopify Partners portal, "
                    "register its credentials in Composio Dashboard, and set COMPOSIO_SHOPIFY_AUTH_CONFIG_ID on the backend."
                ),
            )

        # 2. Check for existing Composio-managed auth config
        data = await self._request("GET", f"/auth_configs?toolkit_slug={slug}&is_composio_managed=true")
        items = data.get("items", [])
        for item in items:
            if (
                item.get("toolkit", {}).get("slug") == slug
                and item.get("status") == "ENABLED"
                and item.get("is_composio_managed") is True
            ):
                return {
                    "id": item["id"],
                    "is_custom_auth": False,
                    "raw": item,
                }

        # 3. If none found, attempt to initialize default managed auth config
        try:
            create_payload = {
                "toolkit": {"slug": slug},
                "auth_scheme": "OAUTH2",
                "is_composio_managed": True,
            }
            res = await self._request("POST", "/auth_configs", json_data=create_payload)
            auth_config = res.get("auth_config", {})
            config_id = auth_config.get("id")
            if config_id:
                return {
                    "id": config_id,
                    "is_custom_auth": False,
                    "raw": res,
                }
        except HTTPException as e:
            logger.warning(f"[ComposioConnection] Auto-init auth_config failed for {slug}: {e.detail}")
            raise HTTPException(
                status_code=400,
                detail=f"Unable to resolve or initialize OAuth configuration for toolkit '{slug}': {e.detail}",
            )

        raise HTTPException(
            status_code=404,
            detail=f"No enabled OAuth configuration found for toolkit '{slug}'.",
        )

    async def create_connection_link(
        self,
        toolkit_slug: str,
        user_id: str,
        alias: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> ConnectionStartResponse:
        slug = toolkit_slug.lower().strip()
        config_info = await self.get_or_create_auth_config(slug)
        auth_config_id = config_info["id"]
        is_custom = config_info.get("is_custom_auth", False)

        payload: Dict[str, Any] = {
            "auth_config_id": auth_config_id,
            "user_id": user_id,
        }
        if alias:
            payload["alias"] = alias
        if callback_url:
            payload["callback_url"] = callback_url

        data = await self._request("POST", "/connected_accounts/link", json_data=payload)

        redirect_url = data.get("redirect_url")
        connected_account_id = data.get("connected_account_id")
        expires_at = data.get("expires_at")

        if not redirect_url or not connected_account_id:
            logger.error(f"[ComposioConnection] Invalid link response from Composio: {data}")
            raise HTTPException(
                status_code=502,
                detail="Upstream Composio service returned incomplete authorization link data.",
            )

        return ConnectionStartResponse(
            redirect_url=redirect_url,
            connected_account_id=connected_account_id,
            expires_at=expires_at,
            toolkit_slug=slug,
            is_custom_auth=is_custom,
            message="Authorization link generated successfully. Direct the user to redirect_url to complete OAuth.",
        )

    async def get_connected_account(
        self,
        connected_account_id: str,
        user_id: str,
    ) -> ConnectedAccountResponse:
        data = await self._request("GET", f"/connected_accounts/{connected_account_id}")

        # Enforce strict ownership validation to prevent cross-tenant enumeration
        account_owner = data.get("user_id")
        if not account_owner or account_owner.strip() != user_id.strip():
            logger.warning(
                f"[ComposioConnection] Unauthorized access attempt: request user '{user_id}' != owner '{account_owner}'"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Connected account '{connected_account_id}' not found for user session.",
            )

        toolkit_info = data.get("toolkit", {})
        toolkit_slug = toolkit_info.get("slug") or "unknown"
        status = data.get("status") or "UNKNOWN"

        return ConnectedAccountResponse(
            id=data["id"],
            toolkit_slug=toolkit_slug,
            status=status,
            status_reason=data.get("status_reason"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            user_id=account_owner,
        )

    async def list_user_connections(self, user_id: str) -> ConnectedAccountListResponse:
        data = await self._request("GET", f"/connected_accounts?user_ids={user_id}")
        items_raw = data.get("items", [])
        results: List[ConnectedAccountResponse] = []

        for item in items_raw:
            # Redact all secrets and only expose safe metadata
            results.append(
                ConnectedAccountResponse(
                    id=item.get("id", ""),
                    toolkit_slug=item.get("toolkit", {}).get("slug", "unknown"),
                    status=item.get("status", "UNKNOWN"),
                    status_reason=item.get("status_reason"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    user_id=item.get("user_id", user_id),
                )
            )

        return ConnectedAccountListResponse(
            items=results,
            total_items=len(results),
        )

    def get_shopify_status(self) -> ShopifyConfigStatusResponse:
        custom_id = settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID
        has_custom = bool(custom_id and custom_id.strip())
        instructions = (
            "Shopify requires Custom OAuth app registration in the Shopify Partners dashboard. "
            "1. Create an app in https://partners.shopify.com. "
            "2. Set Redirect URI to https://backend.composio.dev/api/v1/auth-apps/add. "
            "3. Register your Client ID and Client Secret in Composio Dashboard. "
            "4. Provide the resulting auth_config_id via COMPOSIO_SHOPIFY_AUTH_CONFIG_ID on the backend."
        )
        return ShopifyConfigStatusResponse(
            has_custom_config=has_custom,
            auth_config_id=custom_id if has_custom else None,
            setup_instructions=instructions,
        )


composio_connection_service = ComposioConnectionService()
