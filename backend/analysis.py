"""Request and response models for ABAP analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class TableReference(BaseModel):
    name: str = Field(min_length=1)
    operation: Literal["read", "write", "unknown"] = "unknown"
    reason: str


class Dependency(BaseModel):
    type: Literal["function_module", "method", "perform", "program"]
    name: str = Field(min_length=1)


class RiskItem(BaseModel):
    level: Literal["low", "medium", "high"]
    description: str
    evidence: str | None = None


class AnalysisResponse(BaseModel):
    analysis_mode: Literal["deterministic_static"] = "deterministic_static"
    program_name: str
    purpose: str
    business_summary: str
    tables: list[TableReference]
    dependencies: list[Dependency]
    call_flow: list[str]
    risks: list[RiskItem]
    warnings: list[str] = Field(default_factory=list)
