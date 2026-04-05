# AGENTS.md

## Project Context
This is a data pipeline project that runs on AWS to analyze construction trends in Lima.

The project uses public datasets from Peru's open data platform and compares multiple implementation approaches for ingestion and processing.

## Current Status
- Project scaffold exists
- Source discovery is complete
- Next step: Lambda ingestion MVP

## Source Constraints
- The portal homepage and dataset listing pages return HTML, not JSON
- Some DKAN-style behavior exists, but it is not the most reliable entrypoint for global exploration
- The site is protected by a web application firewall, so bot-like requests may be blocked or behave inconsistently

## Execution Modes

### Architect Mode
Use this mode for system design, component boundaries, trade-offs, and phased planning.
Do not implement full code unless explicitly requested.

### Builder Mode
Use this mode for focused implementation tasks.
Prefer small, testable changes that fit the current project phase.

### Reviewer Mode
Use this mode for reviewing code quality, edge cases, and simplification opportunities.
Do not rewrite large sections unless explicitly requested.

### Researcher Mode
Use this mode for source analysis, documentation review, and option comparison.
Summarize findings with concrete recommendations.

## Model Usage Guidelines
- Use a stronger model for architecture, planning, and complex implementation tasks
- Use a lighter/faster model for smaller implementation or repetitive tasks
- Use parallel work only when the task can be safely split into independent parts

## Agent Rules
- Do not redesign the project unless explicitly asked
- Work only on the requested task scope
- Do not modify files unrelated to the task
- Prefer small, testable modules
- Prefer simple, readable solutions over complex implementations
- Keep solutions runnable locally when possible
- Add logging and clear docstrings
- Avoid introducing new dependencies without strong justification
- Do not update planning or status documents unless explicitly required

## Task Execution Rules
- Each task must include a brief explanation of the design decisions
- Code must be clean, readable, and modular
- Functions should be idempotent when applicable
- Solutions must be runnable locally unless stated otherwise
- Explicitly state assumptions when the task depends on incomplete information

## Planning Files
Read these files before starting implementation work:
- `docs/current_phase.md`
- `docs/task_backlog.md`
- `docs/decisions.md`

## Deliverables Per Task
Unless instructed otherwise, each implementation task should produce:
1. Code changes
2. Minimal tests when feasible
3. Short implementation notes
4. Clear assumptions or follow-up risks