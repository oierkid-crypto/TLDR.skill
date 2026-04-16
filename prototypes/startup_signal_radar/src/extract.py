from __future__ import annotations

from models import ExtractedSignal, NormalizedPost

PAIN_MARKERS = [
    "annoying",
    "frustrating",
    "hate",
    "manual",
    "manually",
    "time-consuming",
    "slow",
    "麻烦",
    "难用",
    "太贵",
    "踩雷",
    "避坑",
    "地推",
    "线下活动",
]
REPLACEMENT_MARKERS = [
    "alternative to",
    "looking for",
    "need a tool",
    "would pay for",
    "有没有更好的",
    "求推荐替代",
    "平替",
]
HEAVY_OPS_MARKERS = [
    "local event",
    "in-person community",
    "field sales",
    "on-site training",
    "线下活动",
    "办社群",
    "地推",
    "上门服务",
]
AI_FIT_MARKERS = [
    "summarize",
    "extract",
    "crm",
    "follow-up",
    "notes",
    "整理",
    "提取",
    "汇总",
    "跟进",
    "自动",
]
WORKFLOW_HINTS = {
    "crm": "crm updates",
    "hubspot": "crm updates",
    "follow-up": "follow-up drafting",
    "call notes": "crm updates",
    "meeting notes": "meeting note cleanup",
    "candidate screening": "candidate screening",
    "resume": "candidate screening",
    "interview notes": "candidate screening",
    "invoice": "freelancer invoicing",
    "invoicing": "freelancer invoicing",
    "payment reminder": "freelancer invoicing",
    "client notes": "client note organization",
    "content repurpose": "content repurposing",
    "repurpose": "content repurposing",
    "skincare": "skincare comparison",
    "routine": "skincare comparison",
    "study planner": "study planning",
    "study schedule": "study planning",
    "meal planning": "meal planning",
    "grocery": "meal planning",
    "社群": "community operations",
    "线下活动": "offline event operations",
}
USER_SEGMENTS = {
    "sales": "sales teams",
    "founder": "founders",
    "recruiter": "recruiters",
    "marketer": "marketers",
    "developer": "developers",
    "creator": "creators",
    "freelancer": "freelancers",
    "shopper": "shoppers",
    "consumer": "consumers",
    "student": "students",
    "parent": "parents",
    "宝妈": "parents",
    "妈妈": "parents",
}


def extract_signal(post: NormalizedPost) -> ExtractedSignal:
    text = post.raw_text.lower()
    pain_points = [marker for marker in PAIN_MARKERS if marker in text]
    workflow = next((value for key, value in WORKFLOW_HINTS.items() if key in text), None)
    user_segment = next((value for key, value in USER_SEGMENTS.items() if key in text), None)
    replacement_intent = any(marker in text for marker in REPLACEMENT_MARKERS)
    heavy_ops_penalty = any(marker in text for marker in HEAVY_OPS_MARKERS)
    ai_fit = any(marker in text for marker in AI_FIT_MARKERS)
    seo_intent = replacement_intent or "how to" in text or "自动" in text
    monetization_hint = "would pay for" in text or "愿意付费" in text

    current_solution = None
    if "gong" in text:
        current_solution = "gong"
    elif "hubspot" in text:
        current_solution = "hubspot"

    return ExtractedSignal(
        normalized_post=post,
        pain_points=pain_points,
        workflow=workflow,
        user_segment=user_segment,
        current_solution=current_solution,
        replacement_intent=replacement_intent,
        seo_intent=seo_intent,
        heavy_ops_penalty=heavy_ops_penalty,
        ai_fit=ai_fit,
        monetization_hint=monetization_hint,
        evidence_excerpt=post.raw_text[:280],
    )
