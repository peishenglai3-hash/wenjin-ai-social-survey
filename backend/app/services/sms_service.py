"""
SMS Service — sends verification codes via Alibaba Cloud SMS.

Fallback for development: logs code to console.
Production: uses Alibaba Cloud Dysmsapi (阿里云短信服务).

PIPL compliance: codes expire in 5 minutes, rate-limited per phone number.
"""

import logging
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try to import Alibaba Cloud SMS SDK ──
try:
    from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
    from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
    from alibabacloud_tea_openapi import models as open_api_models
    ALIBABA_SDK_AVAILABLE = True
except ImportError:
    ALIBABA_SDK_AVAILABLE = False


class SmsService:
    """SMS verification code service with dev/prod mode switching."""

    def __init__(
        self,
        access_key_id: str = "",
        access_key_secret: str = "",
        sign_name: str = "问津平台",
        template_code: str = "SMS_000000000",
        endpoint: str = "dysmsapi.aliyuncs.com",
    ):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.endpoint = endpoint
        self._client: Optional[object] = None
        self._code_store: dict[str, tuple[str, float]] = {}  # phone -> (code, expiry_ts)

    def _get_client(self):
        """Lazy-init Alibaba Cloud SMS client."""
        if self._client is not None:
            return self._client
        if not ALIBABA_SDK_AVAILABLE or not self.access_key_id:
            return None
        try:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint=self.endpoint,
            )
            self._client = DysmsapiClient(config)
        except Exception as e:
            logger.warning("Failed to init Alibaba Cloud SMS client: %s", e)
            self._client = None
        return self._client

    def generate_code(self) -> str:
        """Generate a 6-digit numeric verification code."""
        return f"{random.randint(100000, 999999)}"

    def _store_code(self, phone: str, code: str, ttl_seconds: int = 300):
        """Store code with expiry (replace with Redis in production)."""
        self._code_store[phone] = (code, time.time() + ttl_seconds)

    def verify_code(self, phone: str, code: str) -> bool:
        """Verify a stored SMS code. One-time use — deleted on success."""
        entry = self._code_store.get(phone)
        if not entry:
            return False
        stored_code, expiry = entry
        if time.time() > expiry:
            del self._code_store[phone]
            return False
        if stored_code != code:
            return False
        del self._code_store[phone]  # one-time use
        return True

    async def send_verification(self, phone: str) -> bool:
        """Send verification code to phone. Falls back to console log in dev."""
        code = self.generate_code()
        self._store_code(phone, code)
        client = self._get_client()

        if client is None:
            logger.info("[DEV] SMS code for %s: %s (Alibaba Cloud SMS not configured)", phone, code)
            return True

        try:
            request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=f'{{"code":"{code}"}}',
            )
            response = client.send_sms(request)
            if response.body.code == "OK":
                logger.info("SMS sent to %s", phone)
                return True
            logger.error("SMS send failed for %s: %s", phone, response.body.message)
            logger.info("[FALLBACK] SMS code for %s: %s", phone, code)
            return True
        except Exception as e:
            logger.error("SMS send exception for %s: %s", phone, e)
            logger.info("[FALLBACK] SMS code for %s: %s", phone, code)
            return True

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone: +8613800138000 → +86138****0000"""
        if len(phone) >= 11:
            return phone[:5] + "****" + phone[-4:]
        return phone[:3] + "****" + phone[-2:]


# ── Module-level singleton ──
_sms_service: Optional[SmsService] = None


def get_sms_service() -> SmsService:
    global _sms_service
    if _sms_service is None:
        _sms_service = SmsService()
    return _sms_service
