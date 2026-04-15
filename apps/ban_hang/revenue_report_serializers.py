from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    return value


class RevenueReportSerializer:
    """Serializer JSON don gian cho du lieu bao cao doanh thu."""

    @staticmethod
    def to_json_ready(payload: dict[str, Any]) -> dict[str, Any]:
        return _serialize_value(payload)
