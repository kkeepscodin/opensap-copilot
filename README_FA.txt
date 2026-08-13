PROJECT NORTH — PN-043
Evaluation + Demo Release Candidate v0.5.0

هدف این نسخه:
OpenSAP Copilot را از «نمونه‌ای که کار می‌کند» به «نمونه‌ای که قابل ارزیابی و نمایش است» می‌بریم.
Feature جدید بزرگ اضافه نشده. تمرکز روی Grounding، regression test و demo است.

معماری:
ABAP source
→ deterministic static extraction
→ evidence + uncertainty
→ optional local LLM (Ollama / qwen2.5-coder:3b)
→ deterministic grounding guard
→ structured result
→ UI

تغییرهای PN-043:
1) Prompt سخت‌گیرانه‌تر شده.
2) Generic BAPI_GOODSMVT_CREATE دیگر به تنهایی اجازه inference سناریوی خاص
   مثل transfer / adjustment / goods receipt / goods issue را نمی‌دهد.
3) یک Grounding Guard بعد از LLM اضافه شده؛ یعنی کنترل فقط متکی به prompt نیست.
4) UI در صورت اعمال Guard آن را نشان می‌دهد.
5) سه sample مصنوعی اضافه شده.
6) RUN_EVALUATION.bat اضافه شده و report JSON تولید می‌کند.
7) DEMO_SCRIPT.md یک demo حدود 90 ثانیه‌ای آماده دارد.

----------------------------------------
INSTALL / UPGRADE FROM PN-042.1
----------------------------------------

1) START_BACKEND.bat و START_UI.bat فعلی را ببند.

2) ZIP را Extract کن.

3) محتویات ZIP را روی root فعلی Repository کپی کن و Replace را بزن.
   مسیر فعلی تو معمولاً:
   C:\desktop\Pnorth

4) CHECK_LOCAL_AI.bat را اجرا کن.
   Expected:
   [OK] Local AI prerequisites are ready.

5) START_BACKEND.bat را اجرا کن.
   Expected automated tests:
   6 passed
   Backend version:
   v0.5.0

6) START_UI.bat را اجرا کن.

7) samples\z_inventory_demo.abap را با AI روشن Analyze کن.

Expected:
- provider: ollama-local
- model: qwen2.5-coder:3b
- analysis mode: hybrid-static-plus-local-llm
- Business summary نباید بدون evidence ادعا کند transfer/adjustment/receipt/issue است.
- اگر مدل چنین ادعایی بکند، Grounding Guard باید آن را اصلاح کند.

8) بعد RUN_EVALUATION.bat را اجرا کن.

نتیجه در این فایل ذخیره می‌شود:
evaluation\results\latest_report.json

هدف: همه test caseها PASS شوند.

----------------------------------------
FILES ADDED FOR DEMO / EVALUATION
----------------------------------------

samples\z_inventory_demo.abap
samples\z_audit_update_demo.abap
samples\z_dynamic_call_demo.abap

evaluation\expected.json
evaluation\evaluate.py
RUN_EVALUATION.bat
EVALUATION.md
DEMO_SCRIPT.md
PROJECT_NORTH_STATUS.md

----------------------------------------
IMPORTANT POSITIONING
----------------------------------------

OpenSAP Copilot را به عنوان "first AI for ABAP" معرفی نکن.
Positioning فعلی:

A hybrid, evidence-grounded program-comprehension prototype for legacy ABAP systems.

Core idea:
Evidence first. AI second. Guardrails always.

----------------------------------------
PRIVACY
----------------------------------------

AI enrichment به Ollama روی همین machine می‌رود.
API key لازم نیست.
Source code برای AI enrichment به OpenAI Cloud ارسال نمی‌شود.

----------------------------------------
SUGGESTED GIT COMMIT AFTER LIVE PASS
----------------------------------------

feat: add PN-043 grounding guard and evaluation harness
