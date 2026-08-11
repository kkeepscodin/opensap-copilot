import re
from collections import OrderedDict

from models import AnalysisResponse, Dependency, RiskItem, TableUsage


PROGRAM_PATTERNS = (
    r"(?im)^\s*REPORT\s+([A-Z0-9_/]+)",
    r"(?im)^\s*PROGRAM\s+([A-Z0-9_/]+)",
    r"(?im)^\s*FUNCTION-POOL\s+([A-Z0-9_/]+)",
    r"(?im)^\s*CLASS-POOL\s+([A-Z0-9_/]+)",
)

TABLE_PATTERNS = (
    ("select", r"(?i)\bSELECT\b[\s\S]{0,500}?\bFROM\s+([A-Z0-9_/]+)"),
    ("insert", r"(?i)\bINSERT\s+([A-Z0-9_/]+)"),
    ("update", r"(?i)\bUPDATE\s+([A-Z0-9_/]+)"),
    ("modify", r"(?i)\bMODIFY\s+([A-Z0-9_/]+)"),
    ("delete", r"(?i)\bDELETE\s+FROM\s+([A-Z0-9_/]+)"),
)

DEPENDENCY_PATTERNS = (
    ("function_module", r"(?i)\bCALL\s+FUNCTION\s+['\"]([^'\"]+)['\"]"),
    ("transaction", r"(?i)\bCALL\s+TRANSACTION\s+['\"]([^'\"]+)['\"]"),
    ("method", r"(?i)\bCALL\s+METHOD\s+([A-Z0-9_=/>\-]+)"),
    ("include", r"(?im)^\s*INCLUDE\s+([A-Z0-9_/]+)"),
)

FORM_PATTERN = re.compile(r"(?im)^\s*FORM\s+([A-Z0-9_]+)")
METHOD_PATTERN = re.compile(r"(?im)^\s*METHOD\s+([A-Z0-9_]+)")


def _unique(items: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(items))


def _program_name(source: str) -> str:
    for pattern in PROGRAM_PATTERNS:
        match = re.search(pattern, source)
        if match:
            return match.group(1).upper()
    return "UNKNOWN_PROGRAM"


def _tables(source: str) -> list[TableUsage]:
    detected: dict[tuple[str, str], TableUsage] = {}

    for operation, pattern in TABLE_PATTERNS:
        for name in re.findall(pattern, source):
            normalized = name.upper().strip()
            key = (normalized, operation)
            detected[key] = TableUsage(
                name=normalized,
                operation=operation,
                reason=f"Detected in an ABAP {operation.upper()} statement.",
            )

    return sorted(detected.values(), key=lambda item: (item.name, item.operation))


def _dependencies(source: str) -> list[Dependency]:
    result: list[Dependency] = []

    for dependency_type, pattern in DEPENDENCY_PATTERNS:
        for name in re.findall(pattern, source):
            normalized = name.upper().strip()
            result.append(Dependency(type=dependency_type, name=normalized))

    deduplicated: dict[tuple[str, str], Dependency] = {
        (item.type, item.name): item for item in result
    }
    return sorted(deduplicated.values(), key=lambda item: (item.type, item.name))


def _call_flow(source: str, dependencies: list[Dependency]) -> list[str]:
    flow: list[str] = []

    if re.search(r"(?im)^\s*PARAMETERS\b|^\s*SELECT-OPTIONS\b", source):
        flow.append("Read selection-screen input")

    if re.search(r"(?im)^\s*AT\s+SELECTION-SCREEN\b", source):
        flow.append("Validate user input")

    if re.search(r"(?im)^\s*START-OF-SELECTION\b", source):
        flow.append("Start main processing")

    forms = _unique([item.upper() for item in FORM_PATTERN.findall(source)])
    methods = _unique([item.upper() for item in METHOD_PATTERN.findall(source)])

    for form in forms[:4]:
        flow.append(f"Execute FORM {form}")

    for method in methods[:4]:
        flow.append(f"Execute METHOD {method}")

    called_functions = [
        item.name for item in dependencies if item.type == "function_module"
    ]
    for function_name in called_functions[:4]:
        flow.append(f"Call function module {function_name}")

    if re.search(r"(?i)\bBAPI_TRANSACTION_COMMIT\b|\bCOMMIT\s+WORK\b", source):
        flow.append("Commit the logical unit of work")

    if not flow:
        flow.append("Execute program logic")

    return _unique(flow)[:10]


def _risks(source: str, tables: list[TableUsage], dependencies: list[Dependency]) -> list[RiskItem]:
    risks: list[RiskItem] = []

    write_operations = {"insert", "update", "modify", "delete"}
    written_tables = sorted(
        {table.name for table in tables if table.operation in write_operations}
    )

    if written_tables:
        risks.append(
            RiskItem(
                level="high",
                description=(
                    "The program writes to database objects: "
                    + ", ".join(written_tables[:8])
                    + ". Changes require transaction and data-integrity testing."
                ),
            )
        )

    function_names = {item.name for item in dependencies if item.type == "function_module"}

    if any(name.startswith("BAPI_") for name in function_names):
        risks.append(
            RiskItem(
                level="medium",
                description=(
                    "The program calls one or more BAPIs. Validate return messages, "
                    "commit handling, and rollback behavior."
                ),
            )
        )

    if re.search(r"(?i)\bCOMMIT\s+WORK\b|\bBAPI_TRANSACTION_COMMIT\b", source):
        risks.append(
            RiskItem(
                level="medium",
                description=(
                    "Explicit commit behavior was detected. A change may affect "
                    "transaction boundaries and partial-update behavior."
                ),
            )
        )

    if re.search(r"(?i)\bSUBMIT\b|\bCALL\s+TRANSACTION\b", source):
        risks.append(
            RiskItem(
                level="medium",
                description=(
                    "The program starts another report or transaction. "
                    "Downstream behavior should be regression-tested."
                ),
            )
        )

    if not risks:
        risks.append(
            RiskItem(
                level="low",
                description=(
                    "No direct database write or explicit commit was detected by "
                    "the lightweight MVP analyzer. Manual review is still required."
                ),
            )
        )

    return risks


def _purpose(
    program_name: str,
    tables: list[TableUsage],
    dependencies: list[Dependency],
) -> tuple[str, str]:
    table_names = [item.name for item in tables]
    dependency_names = [item.name for item in dependencies]

    if any(name.startswith("BAPI_GOODSMVT") for name in dependency_names):
        return (
            "Processes an SAP goods-movement workflow.",
            (
                "The program reads or validates inventory-related information and "
                "uses an SAP goods-movement BAPI to post a material transaction."
            ),
        )

    if table_names:
        preview = ", ".join(table_names[:4])
        return (
            f"Processes enterprise data associated with {preview}.",
            (
                f"{program_name} reads or changes SAP data and coordinates the "
                "detected processing steps and dependencies."
            ),
        )

    return (
        "Executes custom ABAP business logic.",
        (
            f"{program_name} contains custom enterprise processing logic. "
            "The current deterministic analyzer found limited explicit database metadata."
        ),
    )


def analyze_abap(source: str) -> AnalysisResponse:
    program_name = _program_name(source)
    tables = _tables(source)
    dependencies = _dependencies(source)
    purpose, business_summary = _purpose(program_name, tables, dependencies)

    return AnalysisResponse(
        program_name=program_name,
        purpose=purpose,
        business_summary=business_summary,
        tables=tables,
        dependencies=dependencies,
        call_flow=_call_flow(source, dependencies),
        risks=_risks(source, tables, dependencies),
    )
