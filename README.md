# opensap-Copilot

**Understand enterprise software in minutes, not days.**

OpenSAP Copilot is an AI-assisted engineering tool that helps developers understand unfamiliar SAP ABAP programs by turning source code into a structured explanation of purpose, business context, tables, call flow, and change risks.

> **Status:** Early MVP development  
> **First supported environment:** SAP ABAP  
> **Goal:** Deliver a focused, working demo for enterprise code understanding.

## The Problem

Enterprise systems often contain years of accumulated business logic, custom programs, and undocumented dependencies. Before changing code safely, engineers must answer:

- What does this program do?
- Which business process does it support?
- Which tables and function modules does it use?
- What is the execution flow?
- What could break if the code changes?

## MVP

The first release focuses on three capabilities:

1. **Code Understanding**
2. **Call-Flow Extraction**
3. **Impact Analysis**

## Demo Flow

```text
Upload ABAP source
        |
Analyze
        |
Program purpose
Business summary
Tables and dependencies
Call flow
Change risks
```

## Planned Architecture

```text
React frontend
      |
FastAPI backend
      |
Prompt and analysis service
      |
LLM provider
      |
Structured JSON
      |
Results dashboard
```

See [docs/architecture.md](docs/architecture.md).

## Current Scope

### Included in v0.1

- ABAP file upload
- AI-assisted program explanation
- Structured JSON analysis
- Table and dependency extraction
- Simplified call-flow output
- Change-risk summary

### Not included in v0.1

- User accounts
- Chat history
- Automatic code modification
- Full ABAP parsing
- Production SAP connectivity

## Technology Direction

- **Frontend:** React
- **Backend:** Python and FastAPI
- **AI integration:** Provider-agnostic LLM service
- **Response format:** Structured JSON

## Project Principles

- Understand before changing.
- Evidence before suggestion.
- Keep the first release small and demonstrable.
- Prefer structured output over free-form chat.
- Never include confidential production code or company data.

## Security and Data Notice

Only synthetic, anonymized, or explicitly permitted sample code may be committed. Never upload proprietary SAP programs, credentials, internal table designs, company names, or production data.

## Roadmap

- [x] Define product vision
- [x] Lock MVP scope
- [x] Create public repository
- [ ] Create backend skeleton
- [ ] Add health-check endpoint
- [ ] Add ABAP analysis endpoint
- [ ] Connect an LLM provider
- [ ] Build the minimal results UI
- [ ] Publish demo v0.1

See [docs/roadmap.md](docs/roadmap.md).

## License

MIT License.

## Author

**Kamyar Hoveishi**  
Software Engineer focused on enterprise systems, performance engineering, and AI-assisted software development.

