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
        return self._put_request(url, headers, payload, f"name/title update for {customer_id}")

    def update_customer_address(
        self,
        customer_id: str,
        address_number: str = "",
        moo: str = "",
        soi: str = "",
        thanon: str = "",
        sub_district: str = "",
        district: str = "",
        province: str = "",
        zip_code: str = "",
        country: str = "TH",
        address_type: str = "A",
        address_format: str = "L",
        address_category: str = "ADD",
        floor: str = "",
        unit: str = "",
        building: str = "",
        village: str = "",
        trok: str = "",
        city: str = "",
        address_line1: str = "",
        address_line2: str = "",
        address_line3: str = "",
        address_line4: str = "",
        state: str = "",
        property_ownership_status: str = "",
        property_type: str = "",
        stay_since: str = "",
        remark: str = "",
    ) -> MobiusResult:
        """Update customer address in Mobius.

        POST /party/cust-profile/address

        Address Types:
            E=Education, F=Census Registration, H=Home, I=ID Card,
            M=ID+Census, O=Office, N=Nationality Home, A=Mailing, T=Temporary

        Address Formats:
            L=Local Standard, B=Building, F=International

        Args:
            customer_id: CIF from search_customer_by_cid()
            address_number: บ้านเลขที่
            moo: หมู่
            soi: ซอย
            thanon: ถนน
            sub_district: แขวง/ตำบล
            district: เขต/อำเภอ
            province: จังหวัด
            zip_code: รหัสไปรษณีย์
            country: ประเทศ (default: TH)
            address_type: ประเภทที่อยู่ (default: A=Mailing)
            address_format: รูปแบบ (default: L=Local Standard)

        Returns:
            MobiusResult with ok=True on success.
        """
        url = f"{self.base_url}/party/cust-profile/address"
        headers = {
            **MOBIUS_HEADERS,
            "requestUID": self._generate_uid(),
            "correlationID": self._generate_uid(),
            "channelCode": "CRDX",
        }

        payload = {
            "customerId": customer_id,
            "addressFormat": address_format,
            "addressType": address_type,
            "addressCategory": address_category,
            "addressNumber": address_number,
            "floor": floor,
            "unit": unit,
            "building": building,
            "village": village,
            "trok": trok,
            "moo": moo,
            "soi": soi,
            "subDistrict": sub_district,
            "district": district,
            "thanon": thanon,
            "province": province,
            "city": city,
            "zipCode": zip_code,
            "country": country,
            "addressLine1": address_line1,
            "addressLine2": address_line2,
            "addressLine3": address_line3,
            "addressLine4": address_line4,
            "state": state,
            "propertyOwnershipStatus": property_ownership_status,
            "propertyType": property_type,
            "staySince": stay_since,
            "remark": remark,
        }

        logger.info(f"Mobius: updating address for customer {customer_id}")
        return self._post_request(url, headers, payload, f"address update for {customer_id}")

    def update_customer_contact(
        self,
        customer_id: str,
        contact_type_code: str,
        contact_information: str,
        contact_category: str = "PRI",
    ) -> MobiusResult:
        """Update customer contact (phone or email) in Mobius.

        POST /party/cust-profile/{customerId}/Contacts

        Contact Type Codes:
            PM = Primary Mobile Phone
            PE = Primary Email

        Contact Category:
            PRI = Primary

        Args:
            customer_id: CIF from search_customer_by_cid()
            contact_type_code: "PM" for phone, "PE" for email
            contact_information: phone number or email address
            contact_category: default "PRI" (Primary)

        Returns:
            MobiusResult with ok=True on success.
        """
        url = f"{self.base_url}/party/cust-profile/{customer_id}/Contacts"
        headers = {
            **MOBIUS_HEADERS,
            "requestUID": self._generate_uid(),
            "correlationID": self._generate_uid(),
            "channelCode": "CRDX",
            "userId": "0014000011",
            "lastUpdateUser": "CCRS",
            "lastupdatechannel": "MB",
            "channelstool": "M",
        }

        payload = {
            "customerId": customer_id,
            "contactTypeCode": contact_type_code,
            "contactInformation": contact_information,
            "contactCategory": contact_category,
        }

        contact_desc = "phone" if contact_type_code == "PM" else "email"
        logger.info(f"Mobius: updating {contact_desc} for customer {customer_id}")
        return self._post_request(url, headers, payload, f"{contact_desc} update for {customer_id}")

    def update_customer_phone(self, customer_id: str, phone_number: str) -> MobiusResult:
        """Update customer primary mobile phone."""
        return self.update_customer_contact(customer_id, "PM", phone_number)

    def update_customer_email(self, customer_id: str, email: str) -> MobiusResult:
        """Update customer primary email."""
        return self.update_customer_contact(customer_id, "PE", email)

    def _post_request(self, url: str, headers: dict, payload: dict, description: str) -> MobiusResult:
        """Execute a POST request with retry logic."""
        customer_id = payload.get("customerId", "")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code in (200, 201):
                    data = resp.json() if resp.text else {}
                    logger.info(f"Mobius: {description} — success")
                    return MobiusResult(ok=True, customer_id=customer_id, status_code=resp.status_code, data=data)

                if resp.status_code >= 500 and attempt < MAX_RETRIES:
                    logger.warning(f"Mobius {description}: HTTP {resp.status_code} (attempt {attempt})")
                    continue

                return MobiusResult(
                    ok=False, customer_id=customer_id,
                    status_code=resp.status_code,
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            except requests.Timeout:
                logger.warning(f"Mobius {description}: timeout (attempt {attempt})")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message="Timeout after 3 retries")
            except requests.RequestException as e:
                logger.error(f"Mobius {description}: request error — {e}")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message=str(e))

        return MobiusResult(ok=False, customer_id=customer_id, message="Max retries exceeded")

    def _put_request(self, url: str, headers: dict, payload: dict, description: str) -> MobiusResult:
        """Execute a PUT request with retry logic."""
        customer_id = payload.get("customerId", "")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.put(url, json=payload, headers=headers, timeout=self.timeout)

                if resp.status_code in (200, 201):
                    data = resp.json() if resp.text else {}
                    logger.info(f"Mobius: {description} — success")
                    return MobiusResult(ok=True, customer_id=customer_id, status_code=resp.status_code, data=data)

                if resp.status_code >= 500 and attempt < MAX_RETRIES:
                    logger.warning(f"Mobius {description}: HTTP {resp.status_code} (attempt {attempt})")
                    continue

                return MobiusResult(
                    ok=False, customer_id=customer_id,
                    status_code=resp.status_code,
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            except requests.Timeout:
                logger.warning(f"Mobius {description}: timeout (attempt {attempt})")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message="Timeout after 3 retries")
            except requests.RequestException as e:
                logger.error(f"Mobius {description}: request error — {e}")
                if attempt == MAX_RETRIES:
                    return MobiusResult(ok=False, customer_id=customer_id, message=str(e))

        return MobiusResult(ok=False, customer_id=customer_id, message="Max retries exceeded")
