from __future__ import annotations
from report_models import DailyNeedsReport, WeeklyNeedsReport


def _judgment_label(value: str) -> str:
    mapping = {
        "credible": "可信",
        "weak": "较弱",
        "unclear": "待确认",
    }
    return mapping.get(value, value)


def _reason_label(value: str) -> str:
    mapping = {
        "repeated mentions": "重复出现",
        "cross-platform evidence": "跨平台同时出现",
        "explicit tool-seeking intent": "存在明确找工具/替代方案意图",
        "concrete workflow friction": "存在具体工作流摩擦",
    }
    return mapping.get(value, value)


def _render_daily_channel(channel_name: str, payload: dict) -> str:
    lines = [f"## {channel_name}"]
    strong = payload.get("strong_signals", [])
    if strong:
        for item in strong:
            assessment = item.get("assessment", {})
            platforms = "、".join(assessment.get("platforms", [])) or "无"
            lines.append(f"- 信号：{item['title']}")
            lines.append(f"  - 概述：{item['summary']}")
            lines.append(
                f"  - 结构化判断：出现频率={assessment.get('frequency_count', 0)}，跨平台={assessment.get('cross_platform', False)}，平台={platforms}，真实需求判断={_judgment_label(assessment.get('real_need_judgment', 'unclear'))}（置信度 {assessment.get('real_need_confidence', 0)}）"
            )
            if assessment.get("why_it_seems_real"):
                lines.append(f"  - 判断依据：{'，'.join(_reason_label(reason) for reason in assessment['why_it_seems_real'])}")
            evidence = item.get("evidence", [])
            if evidence:
                lines.append("  - Evidence（原文）：")
                for ev in evidence[:2]:
                    excerpt = ev.get("excerpt") or ev.get("content")
                    lines.append(f"    - [{ev.get('platform', 'unknown')}] {excerpt}")
    else:
        lines.append(payload.get("no_strong_signal_message") or f"今天没有发现足够强的 {channel_name} 信号。")
    return "\n".join(lines)


def render_daily_user_needs_report(report: dict | DailyNeedsReport) -> str:
    payload = report.model_dump() if hasattr(report, "model_dump") else report
    parts = [f"# 每日用户需求雷达 — {payload['report_date']}"]
    parts.append(_render_daily_channel("2B", payload["channels"]["2b"]))
    parts.append(_render_daily_channel("2C", payload["channels"]["2c"]))
    parts.append(_render_daily_channel("2P", payload["channels"]["2p"]))
    return "\n\n".join(parts)


def _render_weekly_channel(channel_name: str, payload: dict) -> str:
    lines = [f"## {channel_name}"]
    if payload.get("strongest_patterns"):
        for pattern in payload["strongest_patterns"]:
            lines.append(f"- 模式：{pattern}")
        if payload.get("representative_evidence"):
            lines.append("- Evidence（原文）：")
            for ev in payload["representative_evidence"][:3]:
                lines.append(f"  - {ev}")
    else:
        lines.append(payload.get("no_strong_signal_message") or f"本周没有发现足够强的 {channel_name} 持续性信号。")
    return "\n".join(lines)


def render_weekly_user_needs_report(report: dict | WeeklyNeedsReport) -> str:
    payload = report.model_dump() if hasattr(report, "model_dump") else report
    parts = [f"# 每周用户需求周报 — {payload['week_label']}", payload["overall_summary"]]
    parts.append(_render_weekly_channel("2B", payload["channels"]["2b"]))
    parts.append(_render_weekly_channel("2C", payload["channels"]["2c"]))
    parts.append(_render_weekly_channel("2P", payload["channels"]["2p"]))
    return "\n\n".join(parts)
