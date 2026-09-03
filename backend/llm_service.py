import json
import os
import re

import httpx

from models import AIAnalysis, GroundedConclusion, LLMEnrichmentPayload

SYSTEM_INSTRUCTIONS = """
You are the local AI enrichment layer of an enterprise program-comprehension tool.

Your job is NOT to invent business meaning. Your job is to explain an ABAP
program using only:
1. the uploaded source code,
2. deterministic evidence extracted by the application,
3. explicit uncertainty supplied by the application.

Rules:
- Do not claim a SAP business process unless the supplied code/evidence supports it.
- Distinguish facts from likely interpretations.
- Keep summaries concise and useful to a software engineer.
- Do not expose private chain-of-thought.
- used_evidence must contain only exact evidence values included in the input.
- If important runtime/configuration/customizing context is missing, put it in unknowns.
- Do not suggest that static analysis proves runtime behavior.
- A generic goods-movement BAPI does NOT prove a specific scenario such as transfer,
  inventory adjustment, goods receipt, or goods issue. Only name a specific scenario
  when the supplied source/evidence explicitly establishes it.
- If a specific movement scenario is not established, say "goods-movement workflow"
  and list the exact scenario as unknown.
- Do not convert an uncertainty into a factual statement.
- Return only data that matches the requested JSON schema.
""".strip()

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"
DEFAULT_SOURCE_CHAR_LIMIT = 12000

# Scenario terms that are too specific to infer from a generic BAPI alone.
_SCENARIO_PATTERNS = {
    "inventory adjustment": r"\binventory\s+adjustments?\b",
    "transfer": r"\btransfers?\b",
    "goods receipt": r"\bgoods?\s+receipts?\b",
    "goods issue": r"\bgoods?\s+issues?\b",
}


def _build_user_input(source: str, grounded: GroundedConclusion) -> str:
    evidence_values = [item.value for item in grounded.evidence]

    try:
        source_char_limit = int(
            os.getenv("OLLAMA_SOURCE_CHAR_LIMIT", str(DEFAULT_SOURCE_CHAR_LIMIT))
        )
    except ValueError:
        source_char_limit = DEFAULT_SOURCE_CHAR_LIMIT

    source_char_limit = max(2000, min(source_char_limit, 60000))

    payload = {
        "deterministic_conclusion": grounded.conclusion,
        "deterministic_confidence": grounded.confidence,
        "evidence_values": evidence_values,
        "uncertainty": grounded.uncertainty,
        "source_code": source[:source_char_limit],
        "source_truncated_for_local_ai": len(source) > source_char_limit,
    }

    return (
        "Analyze the following evidence and ABAP source. "
        "Produce concise structured enrichment only.\n\n"
        + json.dumps(payload, indent=2)
    )


def _safe_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).strip().rstrip("/")


def _model_name() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()


def _request_ollama(base_url: str, request_payload: dict) -> httpx.Response:
    timeout = httpx.Timeout(90.0, connect=5.0)
    with httpx.Client(timeout=timeout) as client:
        return client.post(f"{base_url}/api/generate", json=request_payload)


def _explicit_support_text(source: str, grounded: GroundedConclusion) -> str:
    return "\n".join(
        [source, grounded.conclusion]
        + [item.value for item in grounded.evidence]
        + [item.statement for item in grounded.evidence]
    ).lower()


def _unsupported_scenario_terms(text: str, support_text: str) -> list[str]:
    unsupported: list[str] = []
    for label, pattern in _SCENARIO_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE) and not re.search(
            pattern, support_text, flags=re.IGNORECASE
        ):
            unsupported.append(label)
    return unsupported


def _safe_technical_summary(grounded: GroundedConclusion) -> str:
    values = [item.value for item in grounded.evidence]
    if values:
        return "Static evidence detected: " + "; ".join(values) + "."
    return "The available static evidence is limited; no scenario-specific technical claim was added."


def _safe_business_summary(grounded: GroundedConclusion) -> str:
    return (
        grounded.conclusion
        + " The specific business scenario cannot be established from the supplied static evidence."
    )


def _apply_grounding_guard(
    parsed: LLMEnrichmentPayload,
    source: str,
    grounded: GroundedConclusion,
) -> tuple[LLMEnrichmentPayload, bool, list[str]]:
    """Post-validate scenario claims so prompt failure does not become product output."""
    support_text = _explicit_support_text(source, grounded)
    notes: list[str] = []

    technical_unsupported = _unsupported_scenario_terms(
        parsed.technical_summary, support_text
    )
    business_unsupported = _unsupported_scenario_terms(
        parsed.business_summary, support_text
    )
    unsupported = sorted(set(technical_unsupported + business_unsupported))

    if not unsupported:
        return parsed, False, notes

    guarded = parsed.model_copy(deep=True)
    guarded.technical_summary = _safe_technical_summary(grounded)
    guarded.business_summary = _safe_business_summary(grounded)

    scenario_unknown = (
        "The exact goods-movement scenario (for example receipt, issue, transfer, "
        "or adjustment) is not established by the supplied static evidence."
    )
    if scenario_unknown not in guarded.unknowns:
        guarded.unknowns.append(scenario_unknown)

    notes.append(
        "Grounding guard removed unsupported scenario-specific interpretation: "
        + ", ".join(unsupported)
        + "."
    )
    return guarded, True, notes


def enrich_with_ai(
    source: str,
    grounded: GroundedConclusion,
    requested: bool,
) -> AIAnalysis:
    model = _model_name()

    if not requested:
        return AIAnalysis(
            requested=False,
            available=False,
            provider="ollama-local",
            model=model,
            message=(
                "Local AI enrichment was not requested. "
                "Deterministic evidence analysis completed."
            ),
        )

    base_url = _safe_base_url()
    schema = LLMEnrichmentPayload.model_json_schema()

    request_payload = {
        "model": model,
        "system": SYSTEM_INSTRUCTIONS,
        "prompt": _build_user_input(source, grounded),
        "format": schema,
        "stream": False,
        "options": {"temperature": 0,
                   "num_predict":400,
                   },
    }

    try:
        response = _request_ollama(base_url, request_payload)
        response.raise_for_status()

        body = response.json()
        raw_output = body.get("response", "")
        if not raw_output.strip():
            raise RuntimeError("Ollama returned an empty response.")

        parsed = LLMEnrichmentPayload.model_validate_json(raw_output)
        parsed, guard_applied, grounding_notes = _apply_grounding_guard(
            parsed, source, grounded
        )

        allowed_evidence = {item.value for item in grounded.evidence}
        safe_used_evidence = [
            value for value in parsed.used_evidence if value in allowed_evidence
        ]

        message = "Local AI enrichment completed with evidence-grounded structured output."
        if guard_applied:
            message += " A deterministic grounding guard corrected an unsupported interpretation."

        return AIAnalysis(
            requested=True,
            available=True,
            provider="ollama-local",
            model=model,
            technical_summary=parsed.technical_summary,
            business_summary=parsed.business_summary,
            change_considerations=parsed.change_considerations,
            unknowns=parsed.unknowns,
            used_evidence=safe_used_evidence,
            grounding_guard_applied=guard_applied,
            grounding_notes=grounding_notes,
            message=message,
        )

    except httpx.ConnectError:
        return AIAnalysis(
            requested=True,
            available=False,
            provider="ollama-local",
            model=model,
            message=(
                "Local AI unavailable: OpenSAP Copilot could not reach Ollama at "
                f"{base_url}. Start Ollama and retry. Deterministic analysis remains valid."
            ),
        )

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = ""
        try:
            detail = exc.response.json().get("error", "")
        except Exception:
            detail = ""

        if status == 404:
            message = (
                f"Ollama is reachable, but model '{model}' was not found. "
                f"Run: ollama pull {model}. Deterministic analysis remains valid."
            )
        else:
            message = (
                f"Local AI request failed with Ollama HTTP {status}. "
                "Deterministic analysis remains valid."
            )
            if detail:
                message += f" Ollama: {detail[:180]}"

        return AIAnalysis(
            requested=True,
            available=False,
            provider="ollama-local",
            model=model,
            message=message,
        )

    except Exception as exc:
        return AIAnalysis(
            requested=True,
            available=False,
            provider="ollama-local",
            model=model,
            message=(
                "Local AI enrichment failed; deterministic analysis remains valid. "
                f"Local provider error: {type(exc).__name__}"
            ),
        )
