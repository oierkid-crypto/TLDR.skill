from __future__ import annotations

from models import ExtractedSignal, NormalizedPost


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms)


def classify_channel_from_post(post: NormalizedPost, taxonomy: dict) -> str | None:
    text = f"{post.title or ''}\n{post.raw_text}".lower()

    category_map = taxonomy.get("audience_categories", {})
    for segment in category_map.get("2b", {}).get("seed_user_segments", []):
        if segment.lower() in text:
            return "2b"
    for segment in category_map.get("2p", {}).get("seed_user_segments", []):
        if segment.lower() in text:
            return "2p"
    for segment in category_map.get("2c", {}).get("seed_user_segments", []):
        if segment.lower() in text:
            return "2c"

    if _contains_any(text, ["sales", "crm", "recruit", "marketing", "small business", "founder"]):
        return "2b"
    if _contains_any(text, ["creator", "freelancer", "indie hacker", "ecommerce", "developer"]):
        return "2p"
    if _contains_any(text, ["shopper", "consumer", "parent", "student", "skincare", "wellness"]):
        return "2c"
    return None


def classify_channel_from_signal(signal: ExtractedSignal, taxonomy: dict) -> str | None:
    if signal.user_segment in {"sales teams", "founders"}:
        return "2b"
    if signal.user_segment in {"developers", "creators", "freelancers", "ecommerce sellers"}:
        return "2p"
    if signal.user_segment in {"parents", "consumers", "students", "shoppers"}:
        return "2c"

    if signal.workflow in {"crm updates", "follow-up drafting"}:
        return "2b"

    return classify_channel_from_post(signal.normalized_post, taxonomy)
