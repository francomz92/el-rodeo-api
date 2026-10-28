"""MercadoPago webhook signature validation.

Extracted from _client.py to reduce file size. Pure function for
HMAC-SHA256 x-signature verification.
"""

import hashlib
import hmac
import re


def validate_signature(
    x_signature: str,
    x_request_id: str,
    data_id: str,
    secret: str,
) -> bool:
    """Validate an IPN webhook x-signature using HMAC-SHA256.

    The MP x-signature header format is: ts=<timestamp>|v1=<hmac_value>

    The data to sign is:
        data_id + "\\n" + data_id + "|" + x_request_id + "\\n" + ts

    Args:
        x_signature: The x-signature header value (ts=...|v1=...).
        x_request_id: The x-request-id header value.
        data_id: The data.id query parameter value.
        secret: The webhook secret key.

    Returns:
        True if the signature is valid.
    """
    if not x_signature or not secret:
        return False

    # Parse ts and v1 from the x-signature header
    ts_match = re.search(r"ts=(\d+)", x_signature)
    v1_match = re.search(r"v1=([A-Fa-f0-9]+)", x_signature)

    if not ts_match or not v1_match:
        return False

    ts = ts_match.group(1)
    expected_hmac = v1_match.group(1)

    # Build the data string to sign
    data_to_sign = f"{data_id}\n{data_id}|{x_request_id}\n{ts}"

    # Compute HMAC-SHA256
    computed = hmac.new(
        key=secret.encode("utf-8"),
        msg=data_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed, expected_hmac)
