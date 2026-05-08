import asyncio
from collections.abc import AsyncGenerator


async def review_stream(
    decision: str = "approved",
    reviewer: str = "admin_sarah",
    rejection_reason: str | None = None,
    speed: float = 1.0,
) -> AsyncGenerator[dict, None]:
    await asyncio.sleep(1.0 / speed)
    event: dict = {
        "stream": "review",
        "decision": decision,
        "reviewer": reviewer,
        "tier": "org_review",
    }
    if decision == "rejected":
        event["rejection_category"] = "POOR_VIDEO_QUALITY"
        event["reason"] = rejection_reason or "Quality metrics failed."
    else:
        event["notes"] = "Good quality footage, diverse gameplay segments."
    yield event
