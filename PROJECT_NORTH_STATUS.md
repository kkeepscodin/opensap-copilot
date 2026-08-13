# Project North — OpenSAP Copilot status

## Current release candidate
**PN-043 · v0.5.0 · Evaluation + Demo Release**

## Locked before PN-043
- deterministic ABAP evidence extraction
- confidence + uncertainty
- local UI
- optional Ollama enrichment with `qwen2.5-coder:3b`
- local/offline-oriented architecture
- graceful deterministic fallback when AI is unavailable

## PN-043 adds
- stricter evidence-grounding prompt
- post-LLM grounding guard for unsupported goods-movement scenarios
- visible guard notes in UI
- 3-sample evaluation suite
- machine-readable evaluation report
- 90-second demo script

## Exit criteria for PN-043
On the user's machine:
1. `START_BACKEND.bat` reports **6 passed**.
2. Inventory sample works with local AI.
3. Business summary does not make unsupported transfer/adjustment/receipt/issue claims.
4. `RUN_EVALUATION.bat` reports all cases PASS.

After those four checks, freeze feature expansion and treat the MVP as application/demo-ready. The next product work should be polish/evaluation only, while the Canada application track runs in parallel.
