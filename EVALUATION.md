# PN-043 Evaluation

PN-043 freezes feature expansion and adds a small repeatable evaluation suite.

## What is measured

1. Deterministic extraction returns the expected program name, tables, and explicit dependencies.
2. Local Ollama enrichment returns structured output.
3. `used_evidence` is restricted to deterministic evidence values.
4. Scenario-specific hallucinations are blocked for the inventory sample.
5. A machine-readable report is written to `evaluation/results/latest_report.json`.

## Test set

- `z_inventory_demo.abap` — read + goods-movement BAPIs; deliberately does **not** establish receipt/issue/transfer/adjustment.
- `z_audit_update_demo.abap` — SELECT + UPDATE, used to test database-write extraction.
- `z_dynamic_call_demo.abap` — contains a dynamic function-module call that the current deterministic regex intentionally does not resolve; this demonstrates explicit static-analysis limits.

## Run

1. Ensure Ollama is running and `qwen2.5-coder:3b` is installed.
2. Run `START_BACKEND.bat` once so the local virtual environment exists. You can close the server afterward.
3. Run `RUN_EVALUATION.bat`.

The evaluation is intentionally small. It is a demo-grade regression/evidence harness, not a claim of research-level benchmark coverage.
