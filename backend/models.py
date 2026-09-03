from typing import Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]
ConfidenceLevel = Literal["low", "medium", "high"]


class EvidenceItem(BaseModel):
    type: str
    value: str
    statement: str


class GroundedConclusion(BaseModel):
    conclusion: str
    confidence: ConfidenceLevel
    evidence: list[EvidenceItem]
    uncertainty: list[str]


class TableUsage(BaseModel):
    name: str
    operation: str
    reason: str


class Dependency(BaseModel):
    type: str
    name: str


class RiskItem(BaseModel):
    level: RiskLevel
    description: str



class LLMSummaryPayload(BaseModel):
    technical_summary: str = Field(
        description="One or two concise technical sentences grounded only in supplied evidence."
    )
    business_summary: str = Field(
        description="One or two concise business-language sentences without unsupported assumptions."
    )

class AIAnalysis(BaseModel):
    requested: bool
    available: bool
    provider: str | None = None
    model: str | None = None
    technical_summary: str | None = None
    business_summary: str | None = None
    change_considerations: list[str] = []
    unknowns: list[str] = []
    used_evidence: list[str] = []
    grounding_guard_applied: bool = False
    grounding_notes: list[str] = []
    message: str


class AnalysisResponse(BaseModel):
    program_name: str
    purpose: str
    business_summary: str
    grounded_conclusion: GroundedConclusion
    tables: list[TableUsage]
    dependencies: list[Dependency]
    call_flow: list[str]
    risks: list[RiskItem]
    ai_analysis: AIAnalysis
    analysis_mode: str
