import re

from models import (
    Dependency,
    EvidenceItem,
    GroundedConclusion,
    RiskItem,
    TableUsage,
)


def find_program_name(source: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:REPORT|PROGRAM|FUNCTION-POOL|CLASS-POOL)\s+([A-Z0-9_/]+)",
        source,
    )
    return match.group(1).upper() if match else "UNKNOWN_PROGRAM"


def extract_tables(source: str) -> list[TableUsage]:
    result: list[TableUsage] = []
    seen: set[tuple[str, str]] = set()

    patterns = [
        ("select", r"(?i)\bSELECT\b[\s\S]{0,500}?\bFROM\s+([A-Z0-9_/]+)"),
        ("insert", r"(?i)\bINSERT\s+([A-Z0-9_/]+)"),
        ("update", r"(?i)\bUPDATE\s+([A-Z0-9_/]+)"),
        ("modify", r"(?i)\bMODIFY\s+([A-Z0-9_/]+)"),
        ("delete", r"(?i)\bDELETE\s+FROM\s+([A-Z0-9_/]+)"),
    ]

    for operation, pattern in patterns:
        for name in re.findall(pattern, source):
            normalized = name.upper()
            key = (normalized, operation)
            if key in seen:
                continue

            seen.add(key)
            result.append(
                TableUsage(
                    name=normalized,
                    operation=operation,
                    reason=f"Detected in an ABAP {operation.upper()} statement.",
                )
            )

    return result


def extract_dependencies(source: str) -> list[Dependency]:
    result: list[Dependency] = []
    seen: set[tuple[str, str]] = set()

    patterns = [
        ("function_module", r"(?i)\bCALL\s+FUNCTION\s+['\"]([^'\"]+)['\"]"),
        ("transaction", r"(?i)\bCALL\s+TRANSACTION\s+['\"]([^'\"]+)['\"]"),
        ("include", r"(?im)^\s*INCLUDE\s+([A-Z0-9_/]+)"),
        ("submit", r"(?i)\bSUBMIT\s+([A-Z0-9_/]+)"),
    ]

    for dependency_type, pattern in patterns:
        for name in re.findall(pattern, source):
            normalized = name.upper()
            key = (dependency_type, normalized)
            if key in seen:
                continue

            seen.add(key)
            result.append(Dependency(type=dependency_type, name=normalized))

    return result


def build_grounded_conclusion(
    tables: list[TableUsage],
    dependencies: list[Dependency],
) -> GroundedConclusion:
    evidence: list[EvidenceItem] = []

    for table in tables[:8]:
        evidence.append(
            EvidenceItem(
                type="database_operation",
                value=f"{table.operation.upper()} {table.name}",
                statement=(
                    f"{table.name} is referenced by a detected "
                    f"{table.operation.upper()} statement."
                ),
            )
        )

    for dependency in dependencies[:8]:
        evidence.append(
            EvidenceItem(
                type=dependency.type,
                value=dependency.name,
                statement=(
                    f"Detected {dependency.type.replace('_', ' ')}: "
                    f"{dependency.name}."
                ),
            )
        )

    names = {item.name for item in dependencies}
    has_goods_movement = any(
        name.startswith("BAPI_GOODSMVT") for name in names
    )
    has_commit = "BAPI_TRANSACTION_COMMIT" in names

    if has_goods_movement and has_commit:
        conclusion = (
            "The program performs or participates in an SAP goods-movement workflow."
        )
        confidence = "high"
    elif has_goods_movement:
        conclusion = (
            "The program likely participates in an SAP goods-movement workflow."
        )
        confidence = "medium"
    elif tables and dependencies:
        conclusion = (
            "The program coordinates custom ABAP processing over detected "
            "SAP data and dependencies."
        )
        confidence = "medium"
    elif tables:
        conclusion = (
            "The program performs custom ABAP data processing over detected SAP objects."
        )
        confidence = "medium"
    else:
        conclusion = (
            "The program contains custom ABAP logic, but available static evidence is limited."
        )
        confidence = "low"

    uncertainty = [
        "No SAP runtime context was analyzed.",
        "Dynamic calls and dynamically constructed SQL may not be detected.",
        "Business meaning is inferred only from the uploaded source and detected technical evidence.",
    ]

    if any(item.type == "include" for item in dependencies):
        uncertainty.append(
            "Referenced INCLUDE source was not automatically expanded."
        )

    return GroundedConclusion(
        conclusion=conclusion,
        confidence=confidence,
        evidence=evidence,
        uncertainty=uncertainty,
    )


def build_call_flow(
    source: str,
    dependencies: list[Dependency],
) -> list[str]:
    flow: list[str] = []

    if re.search(r"(?im)^\s*PARAMETERS\b|^\s*SELECT-OPTIONS\b", source):
        flow.append("Read selection-screen input")

    if re.search(r"(?im)^\s*AT\s+SELECTION-SCREEN\b", source):
        flow.append("Validate user input")

    if re.search(r"(?im)^\s*START-OF-SELECTION\b", source):
        flow.append("Start main processing")

    for dependency in dependencies:
        if dependency.type == "function_module":
            flow.append(f"Call function module {dependency.name}")
        elif dependency.type == "transaction":
            flow.append(f"Start transaction {dependency.name}")
        elif dependency.type == "submit":
            flow.append(f"Submit report {dependency.name}")

    if re.search(
        r"(?i)\bBAPI_TRANSACTION_COMMIT\b|\bCOMMIT\s+WORK\b",
        source,
    ):
        flow.append("Commit the logical unit of work")

    return (flow or ["Execute program logic"])[:12]


def build_risks(
    source: str,
    tables: list[TableUsage],
    dependencies: list[Dependency],
) -> list[RiskItem]:
    risks: list[RiskItem] = []

    if any(
        item.operation in {"insert", "update", "modify", "delete"}
        for item in tables
    ):
        risks.append(
            RiskItem(
                level="high",
                description=(
                    "Database write detected; validate transaction and "
                    "data-integrity behavior."
                ),
            )
        )

    if any(item.name.startswith("BAPI_") for item in dependencies):
        risks.append(
            RiskItem(
                level="medium",
                description=(
                    "BAPI usage detected; validate return messages and "
                    "commit/rollback behavior."
                ),
            )
        )

    if re.search(r"(?i)\bCALL\s+TRANSACTION\b|\bSUBMIT\b", source):
        risks.append(
            RiskItem(
                level="medium",
                description=(
                    "Downstream report or transaction execution was detected; "
                    "regression testing should include downstream behavior."
                ),
            )
        )

    if not risks:
        risks.append(
            RiskItem(
                level="low",
                description=(
                    "No direct database write or downstream execution was detected "
                    "by the current static rules."
                ),
            )
        )

    return risks
