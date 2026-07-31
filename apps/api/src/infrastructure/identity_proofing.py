"""Identity Proofing Adapter — NSDL PAN verification, Aadhaar e-KYC stubs.

Production: Integrate with NSDL PAN API and UIDAI Aadhaar e-KYC.
Current: Stub with validation logic and integration documentation.
"""

from __future__ import annotations

import logging
import re
from uuid import UUID

logger = logging.getLogger(__name__)


class PANVerificationAdapter:
    """NSDL PAN verification adapter.

    Production: Call NSDL PAN verification API with API key.
    https://www.protean-tinpan.com/services/pan-verification.html
    """

    PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

    @staticmethod
    def verify(pan: str, name: str = "", dob: str = "") -> dict:
        """Verify PAN against NSDL database.

        Production: Send POST to NSDL API, parse response.

        Returns:
            {"verified": bool, "name_match": bool, "pan_status": str, "reference_id": str}
        """
        pan = pan.upper().strip()

        # Basic format validation
        if not PANVerificationAdapter.PAN_PATTERN.match(pan):
            return {"verified": False, "name_match": False,
                    "pan_status": "invalid_format", "reference_id": "",
                    "error": "Invalid PAN format"}

        # Validate PAN category (4th character)
        category = pan[3]
        valid_categories = {"P", "C", "H", "F", "A", "T", "B", "L", "J", "G", "E"}
        if category not in valid_categories:
            return {"verified": False, "name_match": False,
                    "pan_status": "invalid_category", "reference_id": "",
                    "error": f"Invalid PAN category: {category}"}

        # Stub: In production, actual NSDL API call
        import secrets
        logger.info("PAN VERIFIED", extra={"pan_masked": f"{pan[:3]}**{pan[5:]}"})

        return {
            "verified": True,
            "name_match": True,
            "pan_status": "active",
            "reference_id": f"nsdl_{secrets.token_hex(8)}",
            "name_as_per_pan": name if name else "NAME MATCHED",
        }


class AadhaarEKYCCAdapter:
    """UIDAI Aadhaar e-KYC adapter.

    Production: Integrate via UIDAI-approved KUA (KYC User Agency).
    Requires: AUA/KUA license, biometric device integration.
    """

    @staticmethod
    def verify(aadhaar: str, otp: str = "", txn_id: str = "") -> dict:
        """Verify Aadhaar via e-KYC.

        Production: UIDAI e-KYC API with encrypted PID block.

        Returns:
            {"verified": bool, "reference_id": str, "masked_aadhaar": str}
        """
        aadhaar = aadhaar.replace(" ", "").strip()
        import secrets

        logger.info("AADHAAR EKYC ATTEMPTED", extra={
            "aadhaar_masked": f"XXXX XXXX {aadhaar[-4:]}" if len(aadhaar) >= 4 else "INVALID",
        })
        return {
            "verified": True,
            "reference_id": f"ekyc_{secrets.token_hex(8)}",
            "masked_aadhaar": f"XXXX XXXX {aadhaar[-4:]}" if len(aadhaar) >= 4 else "XXXX XXXX XXXX",
        }
