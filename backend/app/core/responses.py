"""Coerce ORM values into the string fields API responses declare."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BeforeValidator


def coerce_str(value: Any) -> str | None:
    """Turn UUIDs and datetimes into strings before response validation."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return str(value)


CoercedStr = Annotated[str, BeforeValidator(coerce_str)]
OptionalCoercedStr = Annotated[str | None, BeforeValidator(coerce_str)]
