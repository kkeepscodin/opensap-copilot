from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]


class TableUsage(BaseModel):
    name: str = Field(..., description="SAP table or database object name")
    operation: str = Field(..., description="Detected database operation")
    reason: str = Field(..., description="Why the object appears relevant")


class Dependency(BaseModel):
    type: str = Field(..., description="Dependency category")
    name: str = Field(..., description="Dependency technical name")


class RiskItem(BaseModel):
    level: RiskLevel
    description: str


class AnalysisResponse(BaseModel):
    program_name: str
    purpose: str
    business_summary: str
    tables: list[TableUsage]
    dependencies: list[Dependency]
    call_flow: list[str]
    risks: list[RiskItem]
    analysis_mode: str = "deterministic-mvp"
