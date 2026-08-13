from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SAMPLES = ROOT / "samples"
EXPECTED = ROOT / "evaluation" / "expected.json"
RESULTS = ROOT / "evaluation" / "results"

sys.path.insert(0, str(BACKEND))

from analyzer import (  # noqa: E402
    build_grounded_conclusion,
    extract_dependencies,
    extract_tables,
    find_program_name,
)
from llm_service import enrich_with_ai  # noqa: E402


def check(name: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail}


def normalize(values: list[str]) -> set[str]:
    return {value.upper() for value in values}


def main() -> int:
    cases = json.loads(EXPECTED.read_text(encoding="utf-8"))
    report = {
        "project": "OpenSAP Copilot",
        "milestone": "PN-043",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": [],
    }

    total_checks = 0
    passed_checks = 0

    print("\nOpenSAP Copilot — PN-043 Evaluation")
    print("=" * 48)

    for case in cases:
        source = (SAMPLES / case["file"]).read_text(encoding="utf-8")
        program_name = find_program_name(source)
        tables = extract_tables(source)
        dependencies = extract_dependencies(source)
        grounded = build_grounded_conclusion(tables, dependencies)
        ai = enrich_with_ai(source, grounded, requested=True)

        actual_table_evidence = {
            f"{item.operation.upper()} {item.name}" for item in tables
        }
        actual_dependencies = {item.name for item in dependencies}
        allowed_evidence = {item.value for item in grounded.evidence}

        checks = []
        checks.append(
            check(
                "program_name",
                program_name == case["program_name"],
                f"actual={program_name}",
            )
        )
        checks.append(
            check(
                "deterministic_tables",
                normalize(case["tables"]) == normalize(list(actual_table_evidence)),
                f"actual={sorted(actual_table_evidence)}",
            )
        )
        checks.append(
            check(
                "deterministic_dependencies",
                normalize(case["dependencies"]) == normalize(list(actual_dependencies)),
                f"actual={sorted(actual_dependencies)}",
            )
        )
        checks.append(
            check(
                "local_ai_available",
                ai.available,
                ai.message,
            )
        )

        if ai.available:
            checks.append(
                check(
                    "used_evidence_is_allowlisted",
                    set(ai.used_evidence).issubset(allowed_evidence),
                    f"used={ai.used_evidence}",
                )
            )
            checks.append(
                check(
                    "structured_summaries_present",
                    bool((ai.technical_summary or "").strip())
                    and bool((ai.business_summary or "").strip()),
                )
            )

            business = (ai.business_summary or "").lower()
            forbidden = [
                term
                for term in case["forbidden_unsupported_business_terms"]
                if term.lower() in business
            ]
            checks.append(
                check(
                    "unsupported_scenario_claims_blocked",
                    not forbidden,
                    f"forbidden_found={forbidden}; guard={ai.grounding_guard_applied}",
                )
            )

        case_passed = all(item["passed"] for item in checks)
        report["cases"].append(
            {
                "file": case["file"],
                "passed": case_passed,
                "checks": checks,
                "deterministic_conclusion": grounded.conclusion,
                "deterministic_confidence": grounded.confidence,
                "evidence": sorted(allowed_evidence),
                "ai": ai.model_dump(),
            }
        )

        for item in checks:
            total_checks += 1
            passed_checks += int(item["passed"])

        status = "PASS" if case_passed else "FAIL"
        guard = "guard:on" if ai.grounding_guard_applied else "guard:off"
        print(f"[{status}] {case['file']} · {guard}")
        for item in checks:
            mark = "OK" if item["passed"] else "X"
            print(f"  [{mark}] {item['name']}")
            if not item["passed"] and item.get("detail"):
                print(f"       {item['detail']}")

    report["summary"] = {
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "score_percent": round(100 * passed_checks / total_checks, 1)
        if total_checks
        else 0,
        "all_cases_passed": all(case["passed"] for case in report["cases"]),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    latest = RESULTS / "latest_report.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("-" * 48)
    print(
        f"Score: {passed_checks}/{total_checks} "
        f"({report['summary']['score_percent']}%)"
    )
    print(f"Report: {latest}")

    return 0 if report["summary"]["all_cases_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
