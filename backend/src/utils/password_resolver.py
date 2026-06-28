"""Password resolution for PDFs.

Rules (from 4 hours of painful trial and error):
1. Form 16 password is usually PAN (uppercase). Try PAN first.
2. AIS password is ALWAYS: PAN(lowercase) + DOB(DDMMYYYY).
3. Never ask the user for AIS password — it's always derivable if you have PAN+DOB.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PasswordResolver:
    """Resolves PDF passwords without asking the user."""

    @staticmethod
    def get_form16_candidates(pan: str) -> list[str]:
        """Get candidate passwords for Form 16, ordered by likelihood."""
        candidates = []

        # Most common: PAN in uppercase
        clean_pan = pan.strip().upper()
        if clean_pan:
            candidates.append(clean_pan)

        # PAN in lowercase
        candidates.append(clean_pan.lower())

        # PAN + FY as suffix (some employers use this)
        candidates.append(f"{clean_pan}2526")
        candidates.append(f"{clean_pan}@2526")

        # Employer name patterns (rare, user can manually enter)
        # We don't add employer-specific guesses here

        return candidates

    @staticmethod
    def get_ais_password(pan: str, dob: str) -> str:
        """Compute AIS password. This is ALWAYS correct if PAN+DOB are right.

        Format: pan(lowercase) + dob(DDMMYYYY)
        Example: CFFPM4503N + 25041995 → cffpm4503n25041995
        """
        pan_clean = pan.strip().lower()
        dob_clean = dob.strip()
        return f"{pan_clean}{dob_clean}"

    @staticmethod
    def get_password_hint(file_type: str, pan: str) -> str:
        """Get a user-friendly password hint."""
        if file_type == "form16":
            return f"Try your PAN ({pan.upper()})"
        elif file_type == "ais":
            return "AIS password is auto-computed from your PAN + Date of Birth"
        return "Try your PAN"
