# Roadmap

## Release Goal: v0.1 Demo

Build the smallest impressive version of OpenSAP Copilot.

## Milestone 1 — Repository Foundation

- [x] Create public repository
- [x] Add MIT license
- [x] Add `.gitignore`
- [x] Write README
- [x] Add vision, architecture, and roadmap

## Milestone 2 — Backend Skeleton

- [ ] Create FastAPI application
- [ ] Add `GET /health`
- [ ] Add configuration management
- [ ] Add error-response model
- [ ] Add basic tests

**Done when:** The backend starts with one command and `/health` returns HTTP 200.

## Milestone 3 — Analysis Contract

- [ ] Define request and response models
- [ ] Add file validation
- [ ] Add a synthetic ABAP sample
- [ ] Add deterministic mock analysis

**Done when:** A sample file returns valid structured JSON without an AI provider.

## Milestone 4 — AI Integration

- [ ] Add provider interface
- [ ] Add one provider implementation
- [ ] Add prompt template
- [ ] Validate model output
- [ ] Handle invalid responses

## Milestone 5 — Minimal Frontend

- [ ] Create upload screen
- [ ] Create loading state
- [ ] Create results dashboard
- [ ] Display purpose, tables, call flow, and risks

## Milestone 6 — Demo Release

- [ ] Add safe screenshots
- [ ] Record a 60–90 second demo
- [ ] Improve installation instructions
- [ ] Add known limitations
- [ ] Tag `v0.1.0`
