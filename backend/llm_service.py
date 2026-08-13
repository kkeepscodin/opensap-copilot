import json
import os

from dotenv import load_dotenv

from models import AIAnalysis, GroundedConclusion, LLMEnrichmentPayload

load_dotenv()

SYSTEM_INSTRUCTIONS = """
You are the AI enrichment layer of an enterprise program-comprehension tool.

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
""".strip()


def _build_user_input(
    source: str,
    grounded: GroundedConclusion,
) -> str:
    evidence_values = [item.value for item in grounded.evidence]

    payload = {
        "deterministic_conclusion": grounded.conclusion,
        "deterministic_confidence": grounded.confidence,
        "evidence_values": evidence_values,
        "uncertainty": grounded.uncertainty,
        "source_code": source[:60000],
    }

    return (
        "Analyze the following structured evidence and ABAP source. "
        "Return only the requested structured enrichment.\n\n"
        + json.dumps(payload, indent=2)
    )


def enrich_with_ai(
    source: str,
    grounded: GroundedConclusion,
    requested: bool,
) -> AIAnalysis:
    if not requested:
        return AIAnalysis(
            requested=False,
            available=False,
            message="AI enrichment was not requested. Deterministic evidence analysis completed.",
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-terra").strip()

    if not api_key:
        return AIAnalysis(
            requested=True,
            available=False,
            provider="openai",
            model=model,
            message=(
                "AI enrichment is configured but OPENAI_API_KEY is missing. "
                "Deterministic evidence analysis was returned instead."
            ),
        )

    try:
        # Lazy import keeps deterministic mode runnable even before the SDK is installed.
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": _build_user_input(source, grounded),
                },
            ],
            text_format=LLMEnrichmentPayload,
        )

        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("The model returned no parsed structured output.")

        allowed_evidence = {item.value for item in grounded.evidence}
        safe_used_evidence = [
            value
            for value in parsed.used_evidence
            if value in allowed_evidence
        ]

        return AIAnalysis(
            requested=True,
            available=True,
            provider="openai",
            model=model,
            technical_summary=parsed.technical_summary,
            business_summary=parsed.business_summary,
            change_considerations=parsed.change_considerations,
            unknowns=parsed.unknowns,
            used_evidence=safe_used_evidence,
            message="AI enrichment completed using evidence-grounded structured output.",
        )

    except Exception as exc:
        print("[OPENAI ERROR]", type(exc).__name__, str(exc))
        return AIAnalysis(
            requested=True,
            available=False,
            provider="openai",
            model=model,
            message=(
                "AI enrichment failed; deterministic analysis remains valid. "
                f"Provider error: {type(exc).__name__}"
            ),
        )
