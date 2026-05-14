"""Mobius API Client — Customer profile lookup and update.

Flow:
1. search_customer_by_cid(citizen_id) → get customerId (CIF)
2. update_customer_name(customer_id, title, thai_first, thai_last) → update profile
"""

import uuid
import logging
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
MOBIUS_BASE_URL = "https://kong-uat2-pci-clb.int-np.cardx.co.th/sde-biz-cardx-mobius-gateway-ws/v1"

MOBIUS_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "MBS-Authorization": "Basic Q0JTOjEyMzQ1Njc4OTA=",
    "Authorization": "Basic Y2R4LXVhdDItcGNpLWNpOjREa3EzQlZDVG1UQXFhNTNwbTZmMVE5bWFWY0p2TFZMSUNqeE4xMVY=",
    "channelCode": "CCRS",
}

MAX_RETRIES = 3
TIMEOUT_SECONDS = 30


@dataclass
class MobiusResult:
    """Result of a Mobius API call."""
    ok: bool
    customer_id: str | None = None
    status_code: int | None = None
    message: str | None = None
    data: dict | None = None


class MobiusClient:
    """Client for Mobius customer profile API."""

    def __init__(self, base_url: str = MOBIUS_BASE_URL, timeout: int = TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _generate_uid(self) -> str:
        return str(uuid.uuid4())

    def search_customer_by_cid(self, citizen_id: str) -> MobiusResult:
        """Search customer profile by citizen ID (เลขบัตรประชาชน).

        GET /customer/profile/List?searchBy=ID_NUMBER&idNumber={cid}&idType=P1

        Returns:
            MobiusResult with customer_id (CIF) if found.
        """
        url = f"{self.base_url}/customer/profile/List"
        params = {
            "searchBy": "ID_NUMBER",
            "idNumber": citizen_id,
            "idType": "P1",
        }
        headers = {
            **MOBIUS_HEADERS,
            "requestUID": self._generate_uid(),
            "correlationID": self._generate_uid(),
        }

        logger.info(f"Mobius: searching customer by CID {citizen_id[:4]}***")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)

                if resp.status_code != 200:
                    logger.warning(f"Mobius search: HTTP {resp.status_code} (attempt {attempt})")
                    if resp.status_code >= 500 and attempt < MAX_RETRIES:
                        continue
                    return MobiusResult(ok=False, status_code=resp.status_code, message=f"HTTP {resp.status_code}")

                data = resp.json()
                status = data.get("status", {})

                if status.get("code") != "1000":
                    return MobiusResult(ok=False, message=f"Mobius error: {status.get('message')}", data=data)

                # Extract customerId from first profile
                profiles = data.get("data", {}).get("profileList", [])
                if not profiles:
                    return MobiusResult(ok=False, message="No customer profile found for this CID")

                customer_id = profiles[0].get("customerId")
                if not customer_id:
                    return MobiusResult(ok=False, message="customerId not found in profile response")

                logger.info(f"Mobius: found customerId={customer_id} for CID {citizen_id[:4]}***")
                return MobiusResult(ok=True, customer_id=customer_id, status_code=200, data=data)

            except requests.Timeout:
                logger.warning(f"Mobius search: timeout (attempt {attempt})")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, message="Timeout after 3 retries")
            except requests.RequestException as e:
                logger.error(f"Mobius search: request error — {e}")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, message=str(e))

        return MobiusResult(ok=False, message="Max retries exceeded")

    def update_customer_name(
        self,
        customer_id: str,
        title_code: str | None = None,
        thai_first_name: str | None = None,
        thai_last_name: str | None = None,
        eng_first_name: str | None = None,
        eng_last_name: str | None = None,
    ) -> MobiusResult:
        """Update customer name/title in Mobius.

        PUT /party/cust-profile

        Args:
            customer_id: CIF from search_customer_by_cid()
            title_code: e.g., "MR.", "MRS.", "MISS"
            thai_first_name: New Thai first name
            thai_last_name: New Thai last name
            eng_first_name: New English first name (optional)
            eng_last_name: New English last name (optional)

        Returns:
            MobiusResult with ok=True on success.
        """
        url = f"{self.base_url}/party/cust-profile"
        headers = {
            **MOBIUS_HEADERS,
            "requestUID": self._generate_uid(),
            "deviceId": "sf-case-processor",
            "userId": "640000001",
            "sessionId": self._generate_uid()[:8],
            "accept-language": "EN",
            "channels": "B",
            "channelsTool": "M",
            "lastUpdateUser": "CCRS",
            "channelCode": "CRDX",
        }

        # Build payload — only include fields that are provided
        payload = {"customerId": customer_id}
        if title_code:
            payload["titleCode"] = title_code
        if thai_first_name:
            payload["thaiFirstName"] = thai_first_name
        if thai_last_name:
            payload["thaiLastName"] = thai_last_name
        if eng_first_name:
            payload["engFirstName"] = eng_first_name
        if eng_last_name:
            payload["engLastName"] = eng_last_name

        logger.info(f"Mobius: updating customer {customer_id} — fields: {list(payload.keys())}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.put(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code in (200, 201):
                    data = resp.json() if resp.text else {}
                    logger.info(f"Mobius: update successful for customer {customer_id}")
                    return MobiusResult(ok=True, customer_id=customer_id, status_code=resp.status_code, data=data)

                if resp.status_code >= 500 and attempt < MAX_RETRIES:
                    logger.warning(f"Mobius update: HTTP {resp.status_code} (attempt {attempt})")
                    continue

                # 4xx or final 5xx
                return MobiusResult(
                    ok=False, customer_id=customer_id,
                    status_code=resp.status_code,
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            except requests.Timeout:
                logger.warning(f"Mobius update: timeout (attempt {attempt})")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message="Timeout after 3 retries")
            except requests.RequestException as e:
                logger.error(f"Mobius update: request error — {e}")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message=str(e))

        return MobiusResult(ok=False, customer_id=customer_id, message="Max retries exceeded")
