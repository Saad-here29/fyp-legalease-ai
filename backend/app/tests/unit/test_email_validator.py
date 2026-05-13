"""Unit tests for email_validator — the MX-record gate that fires on
signup. Tests use ALWAYS_VALID_DOMAINS so they don't hit real DNS."""

import pytest

from app.utils.email_validator import EmailValidationError, validate_email_domain


# ============================================================
# UT-EMAIL-001: well-known domains pass without DNS lookup
# ============================================================
def test_gmail_passes_fast_path():
    # Should not raise — gmail.com is in ALWAYS_VALID_DOMAINS
    validate_email_domain("user@gmail.com")


def test_university_passes_fast_path():
    validate_email_domain("student@fast.edu.pk")


# ============================================================
# UT-EMAIL-002: bad format is rejected before any DNS lookup
# ============================================================
def test_missing_at_sign_rejected():
    with pytest.raises(EmailValidationError):
        validate_email_domain("notanemail")


def test_no_tld_rejected():
    with pytest.raises(EmailValidationError):
        validate_email_domain("user@localhost")


def test_empty_string_rejected():
    with pytest.raises(EmailValidationError):
        validate_email_domain("")
