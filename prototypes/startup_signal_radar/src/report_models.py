from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ChannelName = Literal["2b", "2c", "2p"]
RealNeedJudgment = Literal["credible", "weak", "unclear"]


class EvidenceItem(BaseModel):
    platform: Literal["reddit", "x"]
    content: str
    excerpt: str
    url: str


class SignalAssessment(BaseModel):
    frequency_count: int = 0
    cross_platform: bool = False
    platforms: list[str] = Field(default_factory=list)
    real_need_judgment: RealNeedJudgment = "unclear"
    real_need_confidence: float = 0.0
    why_it_seems_real: list[str] = Field(default_factory=list)


class SignalItem(BaseModel):
    signal_id: str
    title: str
    summary: str
    channel: ChannelName
    evidence: list[EvidenceItem] = Field(default_factory=list)
    assessment: SignalAssessment = Field(default_factory=SignalAssessment)


class ChannelDailyReport(BaseModel):
    strong_signals: list[SignalItem] = Field(default_factory=list)
    weak_or_monitor_only: list[SignalItem] = Field(default_factory=list)
    no_strong_signal_message: str | None = None


class DailyNeedsReport(BaseModel):
    report_date: str
    channels: dict[ChannelName, ChannelDailyReport]


class ChannelWeeklyReport(BaseModel):
    strongest_patterns: list[str] = Field(default_factory=list)
    representative_evidence: list[str] = Field(default_factory=list)
    no_strong_signal_message: str | None = None


class WeeklyNeedsReport(BaseModel):
    week_label: str
    overall_summary: str
    channels: dict[ChannelName, ChannelWeeklyReport]
