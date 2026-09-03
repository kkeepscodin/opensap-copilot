import json
import os
import re
import time

import httpx

from models import AIAnalysis, GroundedConclusion, LLMSummaryPayload


SYSTEM_INSTRUCTIONS = """
You are the local explanation layer of an enterprise program-comprehension tool.

A deterministic analyzer has already extracted the technical evidence.
Do not attempt to rediscover every detail of the full program.

Your task is only to produce:
1. a concise technical summary,
2. a concise business-language summary.

Rules:
- Use only the supplied deterministic evidence, uncertainty, and code excerpt.
- Do not invent SAP business meaning.
- Distinguish facts from interpretations.
- Do not claim runtime behavior from static analysis.
- A generic goods-movement BAPI does not prove receipt, issue, transfer,
  or inventory adjustment unless the evidence explicitly establishes it.
- Keep each summary to one or two short sentences.
- Return only data matching the requested JSON schema.
""".strip()


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"
DEFAULT_EXCERPT_CHAR_LIMIT = 2400
MAX_AI_SECONDS = 60.0


_SCENARIO_PATTERNS = {
    "inventory adjustment": r"\binventory\s+adjustments?\b",
    "transfer": r"\btransfers?\b",
    "goods receipt": r"\bgoods?\s+receipts?\b",
    "goods issue": r"\bgoods?\s+issues?\b",
}


def _evidence_keywords(grounded: GroundedConclusion) -> list[str]:
    keywords: set[str] = set()

    ignored = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "MODIFY",
        "DELETE",
    }

    for item in grounded.evidence:
        tokens = re.findall(r"[A-Z][A-Z0-9_/]{2,}", item.value.upper())
        for token in tokens:
            if token not in ignored:
                keywords.add(token)

    return sorted(keywords)


def _build_relevant_excerpt(
    source: str,
    grounded: GroundedConclusion,
) -> str:
    try:
        limit = int(
            os.getenv(
                "OLLAMA_EXCERPT_CHAR_LIMIT",
                str(DEFAULT_EXCERPT_CHAR_LIMIT),
            )
        )
    except ValueError:
        limit = DEFAULT_EXCERPT_CHAR_LIMIT

    limit = max(800, min(limit, 5000))

    lines = source.splitlines()
    keywords = _evidence_keywords(grounded)

    selected_indexes: set[int] = set()

    for index, line in enumerate(lines):
        upper_line = line.upper()

        if any(keyword in upper_line for keyword in keywords):
            start = max(0, index - 2)
            end = min(len(lines), index + 3)

            for nearby in range(start, end):
                selected_indexes.add(nearby)

    if selected_indexes:
        excerpt = "\n".join(
            lines[index]
            for index in sorted(selected_indexes)
        )
    else:
        # When deterministic evidence is limited, provide only a small
        # beginning-of-program fallback rather than the entire source.
        excerpt = source[:limit]

    return excerpt[:limit]


def _build_user_input(
    source: str,
    grounded: GroundedConclusion,
) -> str:
    excerpt = _build_relevant_excerpt(source, grounded)

    evidence = [
        {
            "type": item.type,
            "value": item.value,
            "statement": item.statement,
        }
        for item in grounded.evidence[:12]
    ]

    payload = {
        "deterministic_conclusion": grounded.conclusion,
        "deterministic_confidence": grounded.confidence,
        "evidence": evidence,
        "uncertainty": grounded.uncertainty[:4],
        "relevant_code_excerpt": excerpt,
        "excerpt_is_partial": len(excerpt) < len(source),
    }

    return (
        "Explain the supplied deterministic ABAP analysis. "
        "Do not redo the static analysis. "
        "Return only the two requested concise summaries.\n\n"
        + json.dumps(payload, indent=2)
    )


def _safe_base_url() -> str:
    return os.getenv(
        "OLLAMA_BASE_URL",
        DEFAULT_OLLAMA_URL,
    ).strip().rstrip("/")


def _model_name() -> str:
    return os.getenv(
        "OLLAMA_MODEL",
        DEFAULT_OLLAMA_MODEL,
    ).strip()


def _request_ollama(
    base_url: str,
    request_payload: dict,
) -> httpx.Response:
    timeout = httpx.Timeout(
        connect=5.0,
        read=35.0,
        write=10.0,
        pool=5.0,
    )

    started = time.monotonic()
    generated_parts: list[str] = []

    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            "POST",
            f"{base_url}/api/generate",
            json=request_payload,
        ) as response:

            if response.status_code >= 400:
                response.read()
                response.raise_for_status()

            for line in response.iter_lines():

                if time.monotonic() - started > MAX_AI_SECONDS:
                    raise httpx.ReadTimeout(
                        "Local AI exceeded the generation budget.",
                        request=response.request,
                    )

                if not line:
                    continue

                event = json.loads(line)

                if event.get("error"):
                    raise RuntimeError(
                        f"Ollama error: {event['error']}"
                    )

                piece = event.get("response", "")
                if piece:
                    generated_parts.append(piece)

                if event.get("done"):
                    break

            raw_output = "".join(generated_parts).strip()

            if not raw_output:
                raise RuntimeError(
                    "Ollama returned no generated content."
                )

            return httpx.Response(
                200,
                request=response.request,
                json={"response": raw_output},
            )


def _explicit_support_text(
    source: str,
    grounded: GroundedConclusion,
) -> str:
    return "\n".join(
        [source, grounded.conclusion]
        + [item.value for item in grounded.evidence]
        + [item.statement for item in grounded.evidence]
    ).lower()


def _unsupported_scenario_terms(
    text: str,
    support_text: str,
) -> list[str]:
    unsupported: list[str] = []

    for label, pattern in _SCENARIO_PATTERNS.items():
        if (
            re.search(pattern, text, flags=re.IGNORECASE)
            and not re.search(
                pattern,
                support_text,
                flags=re.IGNORECASE,
            )
        ):
            unsupported.append(label)

    return unsupported


def _safe_technical_summary(
    grounded: GroundedConclusion,
) -> str:
    values = [item.value for item in grounded.evidence]

    if values:
        return (
            "Static evidence detected: "
            + "; ".join(values)
            + "."
        )

    return (
        "The available static evidence is limited; "
        "no scenario-specific technical claim was added."
    )


def _safe_business_summary(
    grounded: GroundedConclusion,
) -> str:
    return (
        grounded.conclusion
        + " The specific business scenario cannot be "
        "established from the supplied static evidence."
    )


def _apply_grounding_guard(
    parsed: LLMSummaryPayload,
    source: str,
    grounded: GroundedConclusion,
) -> tuple[LLMSummaryPayload, bool, list[str]]:

    support_text = _explicit_support_text(
        source,
        grounded,
    )

    technical_unsupported = _unsupported_scenario_terms(
        parsed.technical_summary,
        support_text,
    )

    business_unsupported = _unsupported_scenario_terms(
        parsed.business_summary,
        support_text,
    )

    unsupported = sorted(
        set(
            technical_unsupported
            + business_unsupported
        )
    )

    if not unsupported:
        return parsed, False, []

    guarded = parsed.model_copy(deep=True)

    guarded.technical_summary = (
        _safe_technical_summary(grounded)
    )

    guarded.business_summary = (
        _safe_business_summary(grounded)
    )

    note = (
        "Grounding guard removed unsupported "
        "scenario-specific interpretation: "
        + ", ".join(unsupported)
        + "."
    )

    return guarded, True, [note]


def _build_change_considerations(
    grounded: GroundedConclusion,
) -> list[str]:
    considerations: list[str] = []

    if any(
        item.type == "database_operation"
        for item in grounded.evidence
    ):
        considerations.append(
            "Review detected database access and its "
            "performance and authorization implications before changes."
        )

    if any(
        item.type == "function_module"
        for item in grounded.evidence
    ):
        considerations.append(
            "Review detected function-module interfaces, "
            "return handling, and transaction boundaries before changes."
        )

    if any(
        item.type in {"include", "submit", "transaction"}
        for item in grounded.evidence
    ):
        considerations.append(
            "Inspect detected downstream dependencies "
            "and regression-test affected execution paths."
        )

    if not considerations:
        considerations.append(
            "Review the deterministic evidence and "
            "regression-test affected code paths before changes."
        )

    return considerations[:3]


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
    schema = LLMSummaryPayload.model_json_schema()

    request_payload = {
        "model": model,
        "system": SYSTEM_INSTRUCTIONS,
        "prompt": _build_user_input(
            source,
            grounded,
        ),
        "format": schema,
        "stream": True,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_predict": 220,
        },
    }

    try:
        response = _request_ollama(
            base_url,
            request_payload,
        )

        response.raise_for_status()

        body = response.json()
        raw_output = body.get("response", "")

        if not raw_output.strip():
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        parsed = LLMSummaryPayload.model_validate_json(
            raw_output
        )

        (
            parsed,
            guard_applied,
            grounding_notes,
        ) = _apply_grounding_guard(
            parsed,
            source,
            grounded,
        )

        evidence_values = [
            item.value
            for item in grounded.evidence
        ]

        message = (
            "Local AI enrichment completed with "
            "evidence-grounded structured output."
        )

        if guard_applied:
            message += (
                " A deterministic grounding guard "
                "corrected an unsupported interpretation."
            )

        return AIAnalysis(
            requested=True,
            available=True,
            provider="ollama-local",
            model=model,
            technical_summary=(
                parsed.technical_summary
            ),
            business_summary=(
                parsed.business_summary
            ),
            change_considerations=(
                _build_change_considerations(
                    grounded
                )
            ),
            unknowns=list(
                grounded.uncertainty
            ),
            used_evidence=evidence_values,
            grounding_guard_applied=(
                guard_applied
            ),
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
                "Local AI unavailable: OpenSAP Copilot "
                "could not reach Ollama at "
                f"{base_url}. Start Ollama and retry. "
                "Deterministic analysis remains valid."
            ),
        )

    except httpx.TimeoutException:
        return AIAnalysis(
            requested=True,
            available=False,
            provider="ollama-local",
            model=model,
            message=(
                "Local AI enrichment exceeded the "
                "60-second demo latency budget; "
                "deterministic analysis remains valid."
            ),
        )

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code

        detail = ""

        try:
            detail = (
                exc.response.json().get(
                    "error",
                    "",
                )
            )
        except Exception:
            detail = ""

        if status == 404:
            message = (
                f"Ollama is reachable, but model "
                f"'{model}' was not found. "
                f"Run: ollama pull {model}. "
                "Deterministic analysis remains valid."
            )
        else:
            message = (
                f"Local AI request failed with "
                f"Ollama HTTP {status}. "
                "Deterministic analysis remains valid."
            )

            if detail:
                message += (
                    f" Ollama: {detail[:180]}"
                )

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
                "Local AI enrichment failed; "
                "deterministic analysis remains valid. "
                f"Local provider error: "
                f"{type(exc).__name__}"
            ),
        )
