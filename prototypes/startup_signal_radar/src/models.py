from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OpportunityProblem(BaseModel):
    statement: str
    workflow_context: str
    why_now: str


class TargetUser(BaseModel):
    primary_segment: str
    search_behavior: str
    pain_trigger: str
    current_workarounds: list[str] = Field(default_factory=list)


class SolutionHypothesis(BaseModel):
    product_shape: Literal["saas", "agent", "workflow_tool", "api", "hybrid"]
    ai_role: str
    mvp_scope: str
    key_automation_loop: str | None = None


class FounderFit(BaseModel):
    small_team_buildable: bool
    ops_intensity: Literal["low", "medium", "high"]
    notes: str


class DistributionFit(BaseModel):
    seo_fit: bool
    self_serve_fit: bool
    distribution_notes: str
    suggested_entry_pages: list[str] = Field(default_factory=list)


class BusinessModelFit(BaseModel):
    pricing_shape: str
    repeat_usage: bool
    standardizable: bool
    expansion_paths: list[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    platforms: list[str]
    representative_quotes: list[str]
    signal_summary: str


class OpportunityScores(BaseModel):
    pain_score: float
    buildability_score: float
    ai_leverage_score: float
    distribution_fit_score: float
    business_quality_score: float
    overall_score: float


class OpportunityDecision(BaseModel):
    status: Literal["watchlist", "research_next", "prototype_next", "reject"]
    reason: str
    immediate_next_step: str | None = None


class OpportunityCard(BaseModel):
    opportunity_id: str
    title: str
    problem: OpportunityProblem
    target_user: TargetUser
    ai_solution_hypothesis: SolutionHypothesis
    founder_fit: FounderFit
    distribution_fit: DistributionFit
    business_model_fit: BusinessModelFit
    evidence_summary: EvidenceSummary
    scores: OpportunityScores
    decision: OpportunityDecision
    linked_cluster_ids: list[str] = Field(default_factory=list)


class EngagementMetrics(BaseModel):
    likes: int = 0
    comments: int = 0
    shares: int = 0


class NormalizedPost(BaseModel):
    post_id: str
    platform: Literal["reddit", "x", "xiaohongshu"]
    source_type: str
    source_query: str | None = None
    url: str
    created_at: str
    author_handle: str | None = None
    raw_text: str
    title: str | None = None
    language: str = "unknown"
    community: str | None = None
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)
    metadata: dict = Field(default_factory=dict)


class ExtractedSignal(BaseModel):
    normalized_post: NormalizedPost
    pain_points: list[str] = Field(default_factory=list)
    workflow: str | None = None
    user_segment: str | None = None
    current_solution: str | None = None
    replacement_intent: bool = False
    seo_intent: bool = False
    heavy_ops_penalty: bool = False
    ai_fit: bool = False
    monetization_hint: bool = False
    evidence_excerpt: str
