"""Unit tests for Security bounded context — M9."""

from uuid import uuid4

from src.domain.security.encryption import (
    DataClassification,
    mask_pan,
    mask_aadhaar,
    mask_mobile,
    mask_email,
)


class TestPIIMasking:
    def test_mask_pan(self):
        assert mask_pan("ABCDE1234F") == "ABC**1234F"

    def test_mask_pan_short(self):
        assert mask_pan("ABC") == "***"

    def test_mask_aadhaar(self):
        assert mask_aadhaar("123456789012") == "******789012"

    def test_mask_mobile(self):
        assert mask_mobile("9876543210") == "98****3210"

    def test_mask_email(self):
        assert mask_email("user@example.com") == "u***r@example.com"

    def test_mask_email_short(self):
        assert mask_email("a@b.com") == "***@b.com"


class TestConsentAggregate:
    def test_grant_consent(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        record = agg.grant("tax_computation")
        assert record.is_active
        assert agg.has_consent("tax_computation")

    def test_withdraw_consent(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        agg.grant("tax_computation")
        agg.withdraw("tax_computation")
        assert not agg.has_consent("tax_computation")

    def test_active_purposes(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        agg.grant("tax_computation")
        agg.grant("itr_filing")
        assert len(agg.active_purposes) == 2

    def test_grant_revokes_previous(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        r1 = agg.grant("tax_computation")
        r2 = agg.grant("tax_computation")
        assert not r1.is_active
        assert r2.is_active
        assert r2.version == 2

    def test_no_consent_by_default(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        assert not agg.has_consent("tax_computation")


class TestDataClassification:
    def test_enum_values(self):
        assert DataClassification.RESTRICTED.value == "restricted"
        assert DataClassification.CONFIDENTIAL.value == "confidential"
