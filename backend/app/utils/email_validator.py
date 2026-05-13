"""Email validation — format + DNS MX record check.

Validates that:
1. The email matches a basic RFC-like format.
2. The domain actually has at least one MX record (i.e. it can receive mail).

This does NOT prove that the specific mailbox exists — that's only verifiable
by sending and listening for a bounce — but it does catch fake/typo'd domains
like `xyz123.com` before we create an account.
"""

from __future__ import annotations

import re
from functools import lru_cache

import dns.exception
import dns.resolver

# Common domains we trust without MX lookup (fast-path; saves DNS time).
ALWAYS_VALID_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "yahoo.co.uk",
        "yahoo.co.in",
        "hotmail.com",
        "outlook.com",
        "live.com",
        "icloud.com",
        "me.com",
        "protonmail.com",
        "proton.me",
        "fast.edu.pk",
        "nu.edu.pk",
        "lhr.nu.edu.pk",
        "isb.nu.edu.pk",
        "khi.nu.edu.pk",
        "khi.cfd.nu.edu.pk",
    }
)

_EMAIL_FORMAT_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
)


class EmailValidationError(ValueError):
    """Raised when email format or MX lookup fails. The string message is
    user-safe."""


def _is_format_valid(email: str) -> bool:
    return bool(_EMAIL_FORMAT_RE.match(email or ""))


@lru_cache(maxsize=256)
def _has_mx_record(domain: str) -> bool:
    """Resolve MX (or fall back to A) for the domain. Cached so we don't
    DNS-hammer when the same domain signs up twice."""
    domain = domain.strip().lower()
    if not domain:
        return False
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5.0)
        return any(answers)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        # Some valid mail-receiving domains don't publish MX (RFC 5321
        # implicit MX). Fall back to A/AAAA before declaring it dead.
        try:
            dns.resolver.resolve(domain, "A", lifetime=5.0)
            return True
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.exception.DNSException,
        ):
            return False
    except dns.exception.DNSException:
        # Transient DNS failure — be lenient. Don't punish the user for our
        # resolver being slow.
        return True


def validate_email_domain(email: str) -> None:
    """Raise EmailValidationError on invalid format or unreachable domain."""
    if not _is_format_valid(email):
        raise EmailValidationError("Please enter a valid email address.")

    domain = email.rsplit("@", 1)[-1].lower()
    if domain in ALWAYS_VALID_DOMAINS:
        return

    if not _has_mx_record(domain):
        raise EmailValidationError(
            "This email domain does not appear to exist. "
            "Please use a valid email address."
        )
