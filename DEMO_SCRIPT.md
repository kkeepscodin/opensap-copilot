# OpenSAP Copilot — 90-second demo script

## 0–15 sec — Problem
Legacy ABAP programs are often difficult to understand before changing them. A pure LLM can sound convincing while inventing business meaning.

## 15–35 sec — Evidence first
Open `samples/z_inventory_demo.abap`, leave AI off, and analyze it.
Show:
- detected `SELECT MARA`
- `BAPI_GOODSMVT_CREATE`
- `BAPI_TRANSACTION_COMMIT`
- confidence and uncertainty

Say: **The deterministic layer establishes what the source actually contains.**

## 35–65 sec — Local AI enrichment
Enable **Use local AI enrichment (Ollama)** and analyze again.
Show:
- `ollama-local · qwen2.5-coder:3b`
- technical summary
- business summary
- unknowns
- exact evidence used by AI

Say: **The LLM enriches the explanation, but it is downstream of deterministic evidence. Source code stays on the developer machine.**

## 65–80 sec — Hallucination control
Point to **Grounding guard** when present, or explain that PN-043 post-validates scenario-specific claims.
A generic goods-movement BAPI does not prove receipt, issue, transfer, or adjustment.

## 80–90 sec — Evaluation
Run `RUN_EVALUATION.bat` and show the generated score/report.

Closing line:
**OpenSAP Copilot is a hybrid, evidence-grounded program-comprehension prototype for legacy ABAP systems.**
