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


class LLMEnrichmentPayload(BaseModel):
    technical_summary: str = Field(
        description="Concise technical summary grounded only in provided code/evidence."
    )
    business_summary: str = Field(
        description="Business-language explanation without unsupported SAP assumptions."
    )
    change_considerations: list[str] = Field(
        description="Potential areas a developer should inspect before changing the code."
    )
    unknowns: list[str] = Field(
        description="Important facts that cannot be established from the supplied evidence."
    )
    used_evidence: list[str] = Field(
        description="Exact evidence values supplied to the model that support the summaries."
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
