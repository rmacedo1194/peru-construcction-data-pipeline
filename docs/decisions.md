# Decisions

## 2026-04-03
### Decision
Keep the README high-level and portfolio-oriented.

### Why
The README should explain the project clearly to reviewers, recruiters, and collaborators without mixing in day-to-day implementation control.

### Consequence
Operational guidance will live in AGENTS.md and docs files instead of the README.

---

## 2026-04-03
### Decision
Do not use the public catalogue endpoint as the primary ingestion entrypoint.

### Why
The portal homepage and listing pages return HTML, DKAN-style behavior is inconsistent for global exploration, and the site may block or alter bot-like traffic.

### Consequence
Source discovery and runtime ingestion are treated as separate concerns.

---

## 2026-04-03
### Decision
The Lambda ingestion phase will consume trusted dataset/resource inputs instead of performing broad discovery at runtime.

### Why
This reduces fragility, cost, and runtime complexity, and makes Lambda easier to test locally.

### Consequence
The ingestion contract must accept pre-resolved resource information or direct file URLs.

---

## 2026-04-03
### Decision
Use small planning documents to control agentic development.

### Why
The project will be built iteratively with AI assistance, so the repo needs a compact and explicit source of truth for the current phase and task boundaries.

### Consequence
`docs/current_phase.md`, `docs/task_backlog.md`, and `docs/decisions.md` become part of the delivery workflow.