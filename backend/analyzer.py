"""Lightweight deterministic ABAP analyzer used before AI integration.

This is intentionally not a complete ABAP parser. It provides a stable,
testable response contract so the API and frontend can be built before an LLM
provider is connected.
"""

from __future__ import annotations

import re
from collections import OrderedDict

from app.models.analysis import (
    AnalysisResponse,
    Dependency,
    RiskItem,
    TableReference,
)

_IDENTIFIER = r"[A-Z0-9_/]+"


def _unique(values: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(value.upper() for value in values if value))


def _remove_full_line_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        if line.lstrip().startswith("*"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _program_name(source: str) -> str:
    match = re.search(
        rf"\b(?:REPORT|PROGRAM)\s+({_IDENTIFIER})",
        source,
        flags=re.IGNORECASE,
    )
    return match.group(1).upper() if match else "UNKNOWN_PROGRAM"


def _table_references(source: str) -> list[TableReference]:
    upper = source.upper()
    operations: dict[str, set[str]] = {}

    patterns = [
        ("read", rf"\b(?:FROM|JOIN)\s+({_IDENTIFIER})"),
        ("write", rf"\bUPDATE\s+({_IDENTIFIER})"),
        ("write", rf"\bMODIFY\s+({_IDENTIFIER})"),
        ("write", rf"\bINSERT\s+(?:INTO\s+)?({_IDENTIFIER})"),
        ("write", rf"\bDELETE\s+(?:FROM\s+)?({_IDENTIFIER})"),
    ]

    for operation, pattern in patterns:
        for name in re.findall(pattern, upper):
            operations.setdefault(name, set()).add(operation)

    for declaration in re.findall(r"\bTABLES\s*:\s*([^.]*)\.", upper):
        for name in re.findall(_IDENTIFIER, declaration):
            operations.setdefault(name, set()).add("unknown")

    results: list[TableReference] = []
    for name in sorted(operations):
        detected = operations[name]
        if "write" in detected:
            operation = "write"
            reason = "The source contains a database-changing statement for this object."
        elif "read" in detected:
            operation = "read"
            reason = "The source reads or joins this database object."
        else:
            operation = "unknown"
            reason = "The object is declared, but its exact access mode was not inferred."
        results.append(
            TableReference(name=name, operation=operation, reason=reason)
        )
    return results


def _dependencies(source: str) -> list[Dependency]:
    upper = source.upper()
    results: list[Dependency] = []

    function_modules = _unique(
        re.findall(r"\bCALL\s+FUNCTION\s+['\"]([^'\"]+)['\"]", upper)
    )
    results.extend(
        Dependency(type="function_module", name=name) for name in function_modules
    )

    explicit_methods = re.findall(
        rf"\bCALL\s+METHOD\s+({_IDENTIFIER}(?:=>|->){_IDENTIFIER})", upper
    )
    inline_methods = re.findall(
        rf"\b({_IDENTIFIER}(?:=>|->){_IDENTIFIER})\s*\(", upper
    )
    for name in _unique(explicit_methods + inline_methods):
        results.append(Dependency(type="method", name=name))

    for name in _unique(re.findall(rf"\bPERFORM\s+({_IDENTIFIER})", upper)):
        results.append(Dependency(type="perform", name=name))

    for name in _unique(re.findall(rf"\bSUBMIT\s+({_IDENTIFIER})", upper)):
        results.append(Dependency(type="program", name=name))

    return results


def _call_flow(source: str, dependencies: list[Dependency]) -> list[str]:
    upper = source.upper()
    flow: list[str] = []

    if "INITIALIZATION" in upper:
        flow.append("Initialization")
    if "AT SELECTION-SCREEN" in upper:
        flow.append("Selection-screen validation")
    if "START-OF-SELECTION" in upper:
        flow.append("Main report execution")
    elif re.search(r"\bREPORT\s+", upper):
        flow.append("Program execution")

    if re.search(r"\bSELECT\b", upper):
        flow.append("Database read")
    if dependencies:
        flow.append("Dependency calls")
    if re.search(r"\b(?:INSERT|UPDATE|MODIFY|DELETE)\b", upper):
        flow.append("Database change")
    if "COMMIT WORK" in upper or "BAPI_TRANSACTION_COMMIT" in upper:
        flow.append("Transaction commit")

    return flow or ["Static structure detected; detailed execution flow is not yet available."]


def _risks(source: str, tables: list[TableReference]) -> list[RiskItem]:
    upper = source.upper()
    risks: list[RiskItem] = []

    written_tables = [table.name for table in tables if table.operation == "write"]
    if written_tables:
        risks.append(
            RiskItem(
                level="high",
                description="The program contains direct database-changing statements.",
                evidence=", ".join(written_tables),
            )
        )

    if "COMMIT WORK" in upper or "BAPI_TRANSACTION_COMMIT" in upper:
        risks.append(
            RiskItem(
                level="medium",
                description="The program controls a transaction commit; changes may affect atomicity and rollback behavior.",
                evidence="COMMIT WORK or BAPI_TRANSACTION_COMMIT",
            )
        )

    if re.search(r"CALL\s+FUNCTION\s+\([^)]*\)", upper):
        risks.append(
            RiskItem(
                level="medium",
                description="A dynamic function-module call reduces static traceability.",
                evidence="Dynamic CALL FUNCTION",
            )
        )

    if not risks:
        risks.append(
            RiskItem(
                level="low",
                description="No direct write or commit risk was detected by the deterministic pre-analyzer.",
                evidence="This is not a full semantic safety assessment.",
            )
        )

    return risks


def analyze_abap(source: str) -> AnalysisResponse:
    """Return a deterministic structural analysis for one ABAP source file."""

    cleaned = _remove_full_line_comments(source)
    name = _program_name(cleaned)
    tables = _table_references(cleaned)
    dependencies = _dependencies(cleaned)

    purpose = (
        f"Provide an initial structural map of {name}, including database objects, "
        "callable dependencies, execution stages, and visible change risks."
    )
    business_summary = (
        "This milestone performs deterministic technical inspection only. A business-"
        "level explanation will be generated after the AI provider is connected."
    )

    warnings: list[str] = [
        "This is a lightweight pre-analyzer, not a complete ABAP parser.",
        "Results must not be treated as a production impact assessment.",
    ]
    if name == "UNKNOWN_PROGRAM":
        warnings.append("No REPORT or PROGRAM declaration was detected.")

    return AnalysisResponse(
        program_name=name,
        purpose=purpose,
        business_summary=business_summary,
        tables=tables,
        dependencies=dependencies,
        call_flow=_call_flow(cleaned, dependencies),
        risks=_risks(cleaned, tables),
        warnings=warnings,
    )
