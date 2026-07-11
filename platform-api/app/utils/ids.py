from __future__ import annotations

import secrets
import time
import uuid


def uuid7() -> uuid.UUID:
    """Return a UUIDv7-compatible identifier.

    Python 3.11 does not provide uuid.uuid7. This implementation follows the
    UUIDv7 layout: 48-bit Unix epoch milliseconds, version 7, RFC 4122 variant,
    and random remaining bits.
    """

    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    value = timestamp_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return uuid.UUID(int=value)


def new_resource_id() -> str:
    return str(uuid7())


def new_resource_version() -> str:
    return str(uuid7())
