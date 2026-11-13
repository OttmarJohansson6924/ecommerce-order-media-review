from dataclasses import dataclass
import re
from typing import Any

from infrai_image_client import InfraiImageClient, infrai_image_upload


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    status: str
    customer_message: str


@dataclass(frozen=True)
class ModerationDecision:
    publish: bool
    reason: str
    image_id: tuple[str, ...] | None = None


def screen_caption(caption: str) -> ModerationDecision:
    cleaned = " ".join(caption.split())
    if not cleaned:
        return ModerationDecision(False, "caption is empty")
    blocked_terms = {"weapon", "hate", "scam"}
    if any(re.search(rf"\b{re.escape(term)}\b", cleaned.lower()) for term in blocked_terms):
        return ModerationDecision(False, "caption needs review")
    return ModerationDecision(True, "caption accepted")


def prepare_order_media(
    client: InfraiImageClient,
    order_id: str,
    filename: str,
    image_data: str,
    caption: str,
) -> tuple[ModerationDecision, OrderUpdate]:
    decision = screen_caption(caption)
    if not decision.publish:
        return decision, OrderUpdate(order_id, "review", "Your photo is waiting for a content review.")
    image_id = infrai_image_upload(client, image_data, filename)
    return (
        ModerationDecision(True, decision.reason, image_id),
        OrderUpdate(order_id, "ready", "Your photo is ready for the order update."),
    )


def receipt_payload(order_id: str, decision: ModerationDecision, update: OrderUpdate) -> dict[str, Any]:
    return {"order_id": order_id, "media_status": update.status, "published": decision.publish, "reason": decision.reason}
