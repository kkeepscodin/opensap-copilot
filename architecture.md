# Architecture

## Objective

The v0.1 architecture is optimized for speed, clarity, and replaceability.

## High-Level Flow

```text
React UI
   ↓
FastAPI REST API
   ↓
Analysis service
   ↓
Prompt builder
   ↓
LLM provider adapter
   ↓
Response validator
   ↓
Structured JSON
   ↓
React results view
```

## Initial Endpoints

```text
GET  /health
POST /api/v1/analyze
```

## Response Contract

```json
{
  "program_name": "Z_SAMPLE_PROGRAM",
  "purpose": "Short technical purpose",
  "business_summary": "Explanation for a non-technical stakeholder",
  "tables": [
    {
      "name": "MARA",
      "operation": "read",
      "reason": "Material master lookup"
    }
  ],
  "dependencies": [
    {
      "type": "function_module",
      "name": "BAPI_GOODSMVT_CREATE"
    }
  ],
  "call_flow": [
    "Selection screen",
    "Input validation",
    "Business processing",
    "BAPI call",
    "Commit"
  ],
  "risks": [
    {
      "level": "medium",
      "description": "Changing movement logic may affect inventory posting."
    }
  ]
}
```

## Non-Goals for v0.1

- full ABAP grammar parsing,
- repository-wide dependency analysis,
- authentication,
- database persistence,
- automatic code changes,
- production SAP connectivity.

## Security Constraints

- Never commit production ABAP source.
- Use only synthetic or permitted samples.
- Keep API keys in environment variables.
- Do not log uploaded source by default.
- Limit upload size.

## Key Design Decisions

### Structured JSON Instead of Chat

The demo should look like a product, not a generic chatbot.

### One Analysis Endpoint

A single endpoint keeps the first version small.

### No Custom Parser Initially

The first release uses LLM-assisted analysis plus lightweight deterministic extraction where useful.
