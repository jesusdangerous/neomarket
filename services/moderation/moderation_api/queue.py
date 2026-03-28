import json
from uuid import UUID

import requests
from django.conf import settings

from .models import ModerationCard


def _parse_event_payload(data: dict):
    raw_payload = data.get("payload")
    if raw_payload:
        try:
            return json.loads(raw_payload)
        except (TypeError, ValueError):
            return {}
    return {}


def parse_event(message_fields: dict) -> dict:
    fields = {k.decode("utf-8") if isinstance(k, bytes) else k: v for k, v in message_fields.items()}
    normalized = {
        (k.decode("utf-8") if isinstance(k, bytes) else k):
        (v.decode("utf-8") if isinstance(v, bytes) else v)
        for k, v in fields.items()
    }

    payload = _parse_event_payload(normalized)
    product_id = normalized.get("product_id") or payload.get("product_id")
    event_type = (normalized.get("event_type") or payload.get("event_type") or "UPDATED").upper()

    snapshot_before = payload.get("snapshot_before")
    snapshot_after = payload.get("snapshot_after")

    return {
        "product_id": product_id,
        "event_type": event_type,
        "snapshot_before": snapshot_before,
        "snapshot_after": snapshot_after,
    }


def fetch_b2b_snapshot(product_id):
    template = settings.B2B_PRODUCT_URL_TEMPLATE
    if not template:
        return None

    url = template.format(product_id=product_id)
    try:
        response = requests.get(url, timeout=settings.B2B_REQUEST_TIMEOUT)
    except requests.RequestException:
        return None

    if not response.ok:
        return None

    try:
        return response.json()
    except ValueError:
        return None


def enqueue_from_event(event: dict):
    if not event.get("product_id"):
        return None

    try:
        product_id = UUID(str(event["product_id"]))
    except (TypeError, ValueError):
        return None

    event_type = event.get("event_type", "UPDATED")
    if event_type not in {ModerationCard.EventType.CREATED, ModerationCard.EventType.UPDATED}:
        event_type = ModerationCard.EventType.UPDATED

    snapshot_after = event.get("snapshot_after") or fetch_b2b_snapshot(product_id) or {"id": str(product_id)}

    return ModerationCard.objects.create(
        product_id=product_id,
        event_type=event_type,
        snapshot_before=event.get("snapshot_before"),
        snapshot_after=snapshot_after,
    )
