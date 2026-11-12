"""
Security and Secret Redaction Utilities.

Protects against credential leakage in API responses, logs, and storage.
Ensures that OAuth client secrets, API keys, access/refresh tokens, and private
credentials are never exposed in public responses or log files.
"""
import re
from typing import Any, Dict, List, Set, Union

REDACTED_PLACEHOLDER = "[REDACTED]"

# Safe key exceptions: keys that may contain the substring 'secret' or 'key' but are descriptive flags/notes
SAFE_KEY_EXCEPTIONS: Set[str] = {
    "requires_client_secret",
    "client_secret_required",
    "has_client_secret",
    "client_secret_notes",
    "secret_rotation_days",
    "auth_schemes",
    "composio_managed_auth_schemes",
    "auth_config_details",
    "composio_managed_auth",
    "no_auth",
    "mode",
    "auth_mode",
    "routing_key",
    "primary_key",
}

# Explicit exact match names for credential fields (normalized lowercase without underscores/hyphens)
SENSITIVE_KEY_NAMES: Set[str] = {
    "clientsecret",
    "clientsecrets",
    "secret",
    "secrets",
    "secretkey",
    "accesstoken",
    "refreshtoken",
    "authtoken",
    "bearertoken",
    "idtoken",
    "token",
    "tokens",
    "apikey",
    "apikeys",
    "xapikey",
    "password",
    "passwd",
    "credential",
    "credentials",
    "privatekey",
    "privatekeyid",
    "authorization",
    "authheader",
    "signature",
    "sessionsecret",
}

# Substring patterns that trigger redaction in credential key names
SENSITIVE_SUBSTRINGS = (
    "secret",
    "password",
    "passwd",
    "private_key",
    "privatekey",
)

# Known high-entropy token value patterns (regex for raw credential strings)
SENSITIVE_VALUE_REGEX = re.compile(
    r"(-----BEGIN [A-Z ]+PRIVATE KEY-----|"
    r"ghp_[A-Za-z0-9_]{36,}|"
    r"xox[baprs]-[0-9A-Za-z\-]{10,}|"
    r"AIza[0-9A-Za-z\-_]{35}|"
    r"ya29\.[0-9A-Za-z\-_]+)",
    re.IGNORECASE
)


def _is_sensitive_key(key: str) -> bool:
    """Determine whether a dictionary key represents an actual credential field."""
    if not isinstance(key, str):
        return False

    cleaned = key.strip().lower()

    # Check safe exceptions first (e.g. requires_client_secret, client_secret_notes)
    if cleaned in SAFE_KEY_EXCEPTIONS or cleaned.startswith("requires_") or cleaned.endswith("_required"):
        return False

    normalized = cleaned.replace("_", "").replace("-", "")

    # Check exact match set
    if normalized in SENSITIVE_KEY_NAMES:
        return True

    # Check substring matches
    for sub in SENSITIVE_SUBSTRINGS:
        if sub in cleaned:
            return True

    # Check suffix matches (e.g. "service_token", "consumer_key", "api_key")
    if cleaned.endswith("_token") or cleaned.endswith("token"):
        # Exception: tokens counter/metrics like "total_tokens", "input_tokens", "prompt_tokens"
        if not (cleaned.endswith("_tokens") or cleaned in ("totaltokens", "inputtokens", "prompttokens", "outputtokens")):
            return True

    if cleaned.endswith("_key") or cleaned.endswith("key"):
        if any(term in cleaned for term in ("api", "secret", "private", "access", "auth")):
            return True

    return False


def _is_sensitive_value(val: str) -> bool:
    """Check if a string value matches known high-entropy token/key formats."""
    if not isinstance(val, str) or len(val) < 16:
        return False
    return bool(SENSITIVE_VALUE_REGEX.search(val))


def redact_sensitive_data(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively walk arbitrary data structures (dicts, lists, tuples)
    and replace sensitive keys or values with [REDACTED].

    Never modifies boolean flags, integer counters, or safe structural metadata.
    """
    if max_depth <= 0:
        return data

    if isinstance(data, dict):
        redacted_dict: Dict[str, Any] = {}
        for k, v in data.items():
            str_key = str(k)

            # Never redact booleans or numeric values (they are flags or metrics, not credentials)
            if isinstance(v, (bool, int, float)) and not isinstance(v, str):
                redacted_dict[str_key] = v
            elif _is_sensitive_key(str_key):
                redacted_dict[str_key] = REDACTED_PLACEHOLDER
            elif isinstance(v, (dict, list, tuple)):
                redacted_dict[str_key] = redact_sensitive_data(v, max_depth=max_depth - 1)
            elif isinstance(v, str) and _is_sensitive_value(v):
                redacted_dict[str_key] = REDACTED_PLACEHOLDER
            else:
                redacted_dict[str_key] = v
        return redacted_dict

    if isinstance(data, list):
        return [
            REDACTED_PLACEHOLDER if isinstance(item, str) and _is_sensitive_value(item)
            else redact_sensitive_data(item, max_depth=max_depth - 1)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            REDACTED_PLACEHOLDER if isinstance(item, str) and _is_sensitive_value(item)
            else redact_sensitive_data(item, max_depth=max_depth - 1)
            for item in data
        )

    if isinstance(data, str) and _is_sensitive_value(data):
        return REDACTED_PLACEHOLDER

    return data
