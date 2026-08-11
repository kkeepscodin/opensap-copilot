import re
from models import AnalysisResponse, Dependency, RiskItem, TableUsage

def analyze_abap(source: str) -> AnalysisResponse:
    report = re.search(r"(?im)^\s*(?:REPORT|PROGRAM)\s+([A-Z0-9_/]+)", source)
    program_name = report.group(1).upper() if report else "UNKNOWN_PROGRAM"

    tables = []
    seen_tables = set()
    for op, pattern in [
        ("select", r"(?i)\bSELECT\b[\s\S]{0,500}?\bFROM\s+([A-Z0-9_/]+)"),
        ("insert", r"(?i)\bINSERT\s+([A-Z0-9_/]+)"),
        ("update", r"(?i)\bUPDATE\s+([A-Z0-9_/]+)"),
        ("modify", r"(?i)\bMODIFY\s+([A-Z0-9_/]+)"),
        ("delete", r"(?i)\bDELETE\s+FROM\s+([A-Z0-9_/]+)")
    ]:
        for name in re.findall(pattern, source):
            key = (name.upper(), op)
            if key not in seen_tables:
                seen_tables.add(key)
                tables.append(TableUsage(
                    name=name.upper(),
                    operation=op,
                    reason=f"Detected in an ABAP {op.upper()} statement."
                ))

    dependencies = []
    seen_deps = set()
    for dep_type, pattern in [
        ("function_module", r"(?i)\bCALL\s+FUNCTION\s+['\"]([^'\"]+)['\"]"),
        ("transaction", r"(?i)\bCALL\s+TRANSACTION\s+['\"]([^'\"]+)['\"]"),
        ("include", r"(?im)^\s*INCLUDE\s+([A-Z0-9_/]+)")
    ]:
        for name in re.findall(pattern, source):
            key = (dep_type, name.upper())
            if key not in seen_deps:
                seen_deps.add(key)
                dependencies.append(Dependency(type=dep_type, name=name.upper()))

    call_flow = []
    if re.search(r"(?im)^\s*PARAMETERS\b|^\s*SELECT-OPTIONS\b", source):
        call_flow.append("Read selection-screen input")
    if re.search(r"(?im)^\s*START-OF-SELECTION\b", source):
        call_flow.append("Start main processing")
    for dep in dependencies:
        if dep.type == "function_module":
            call_flow.append(f"Call function module {dep.name}")
    if re.search(r"(?i)\bBAPI_TRANSACTION_COMMIT\b|\bCOMMIT\s+WORK\b", source):
        call_flow.append("Commit the logical unit of work")
    if not call_flow:
        call_flow = ["Execute program logic"]

    risks = []
    if any(t.operation in {"insert","update","modify","delete"} for t in tables):
        risks.append(RiskItem(
            level="high",
            description="Database write detected. Transaction and data-integrity testing are required."
        ))
    if any(d.name.startswith("BAPI_") for d in dependencies):
        risks.append(RiskItem(
            level="medium",
            description="BAPI usage detected. Validate return messages and commit/rollback behavior."
        ))
    if not risks:
        risks.append(RiskItem(
            level="low",
            description="No direct write was detected by the lightweight analyzer. Manual review is still required."
        ))

    dep_names = [d.name for d in dependencies]
    if any(name.startswith("BAPI_GOODSMVT") for name in dep_names):
        purpose = "Processes an SAP goods-movement workflow."
        summary = "The program reads or validates inventory information and uses an SAP goods-movement BAPI to post a material transaction."
    elif tables:
        purpose = "Processes enterprise data in a custom ABAP workflow."
        summary = f"{program_name} reads or changes SAP data and coordinates the detected processing steps."
    else:
        purpose = "Executes custom ABAP business logic."
        summary = f"{program_name} contains custom enterprise processing logic."

    return AnalysisResponse(
        program_name=program_name,
        purpose=purpose,
        business_summary=summary,
        tables=tables,
        dependencies=dependencies,
        call_flow=call_flow[:10],
        risks=risks,
    )
