from __future__ import annotations

from pathlib import Path

import yaml


def load_taxonomy(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text())


def audience_seed_segments(taxonomy: dict, audience_category: str | None) -> list[str]:
    if not audience_category:
        return []
    category = taxonomy.get("audience_categories", {}).get(audience_category, {})
    return list(category.get("seed_user_segments", []))


def build_queries(
    taxonomy: dict,
    *,
    platform: str,
    tool_or_category: str,
    workflow: str,
    user_segment: str,
    audience_category: str | None = None,
) -> list[str]:
    templates = taxonomy.get("query_templates", {})
    queries = []

    replacement = templates.get("replacement_template", "")
    if replacement:
        queries.append(replacement.replace("<tool_or_category>", tool_or_category))

    repetitive = templates.get("repetitive_workflow_template", "")
    if repetitive:
        queries.append(repetitive.replace("<workflow>", workflow))

    search_intent_phrases = taxonomy["positive_signal_groups"]["distribution_hints"]["search_intent_phrases"]
    if search_intent_phrases:
        phrase = search_intent_phrases[0]
        queries.append(f'{user_segment} {phrase} {workflow}')

    related_segments = [segment for segment in audience_seed_segments(taxonomy, audience_category) if segment != user_segment]
    for related_segment in related_segments[:2]:
        queries.append(f'{related_segment} best tool for {workflow}')

    if audience_category:
        queries.append(f'{audience_category} {tool_or_category} {workflow}')

    if platform == "xiaohongshu":
        chinese = templates.get("chinese_consumption_template", "")
        if chinese:
            queries.append(chinese.replace("<品类词/场景词>", tool_or_category))

    downrank_terms = set()
    for lang_markers in taxonomy["downrank_signal_groups"]["heavy_ops_markers"].values():
        downrank_terms.update(lang_markers)

    filtered = [q for q in queries if not any(term in q for term in downrank_terms)]
    return filtered
