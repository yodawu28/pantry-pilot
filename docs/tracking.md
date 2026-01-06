# Tracking Playbook — PantryPilot

This document defines the single source of truth for tracking progress in PantryPilot.
We will track using docs only (no GitHub milestones required).

---

## 1) Tracking Principles
- Everything trackable lives in `docs/`.
- Each week has:
  - a weekly plan (checklist)
  - a weekly devlog (what shipped + metrics + learnings)
- A task is only “done” if it meets the Definition of Done (DoD).

---

## 2) Folder Structure
Recommended:
- `docs/roadmap.md` — 6-week roadmap (high-level)
- `docs/tracking.md` — this playbook (rules + workflow)
- `docs/devlog-template.md` — template for weekly devlogs
- `docs/devlogs/` — weekly devlogs
- `docs/plans/` — weekly plans (optional but recommended)

Example tree:

    docs/
      roadmap.md
      tracking.md
      devlog-template.md
      devlogs/
        2026-W01.md
        2026-W02.md
      plans/
        2026-W01-plan.md
        2026-W02-plan.md

If you want to keep it simpler, you can skip `docs/plans/` and only use devlogs.

---

## 3) Naming Convention (Vietnam timezone-friendly)
Use ISO week format:
- Devlog: `docs/devlogs/YYYY-WW.md`  
  Example: `docs/devlogs/2026-W02.md`
- Weekly plan: `docs/plans/YYYY-WW-plan.md`  
  Example: `docs/plans/2026-W02-plan.md`

---

## 4) Weekly Workflow (Minimal and Repeatable)

### Day 1 — Plan (10 minutes)
1) Copy `docs/devlog-template.md` → `docs/devlogs/YYYY-WW.md`
2) Fill:
   - Week, Date range, Focus theme
   - Goals for this week (3–6 items)
3) (Optional) Create `docs/plans/YYYY-WW-plan.md` with a more detailed checklist.

### During the week — Execute (daily)
- Work in small chunks.
- Keep commits small and descriptive.
- If you discover new tasks, add them to:
  - Next week plan, or Backlog / Ideas (in the devlog).

### Last day of the week — Ship (30–60 minutes)
1) Ensure the demo works locally via docker compose.
2) Add screenshots/GIFs to `docs/assets/` (optional) and link in devlog.
3) Update the devlog sections:
   - What I shipped
   - Metrics
   - Bugs / Issues
   - What I learned
   - Next week plan

---

## 5) Definition of Done (DoD)
A task is considered DONE only if:

### Required
- [ ] Code implemented
- [ ] Runs locally (docker compose or documented local steps)
- [ ] Basic error handling (doesn’t crash on common failures)
- [ ] Documentation updated (README or relevant docs)

### At least one proof
Choose at least one:
- [ ] Screenshot / GIF / short demo video
- [ ] Unit test or integration test
- [ ] Example request/response (API) stored in docs

### If the task is ML-related
- [ ] Include at least 1 metric (even a simple spot-check)

---

## 6) Progress Tracking Rules

### Rule A — Keep weekly goals small
- Target 3–6 checkboxes per week.
- Prefer shipping end-to-end slices rather than many partial modules.

### Rule B — Always maintain a runnable demo
At any point, you should be able to:
- `docker compose up`
- open Streamlit
- click through at least one happy-path flow (even if minimal)

### Rule C — Track metrics early (even if rough)
Minimum metrics by phase:
- Week 1: upload success rate
- Week 2: parse success rate + correction rate
- Week 3: normalization spot-check accuracy
- Week 4: retrieval latency (rough) + #recipes indexed
- Week 5: avg coverage top-k
- Week 6: evaluation on gold set

---

## 7) What to Record Each Week (Minimum)
In every weekly devlog, record:
- What shipped
- Metrics snapshot
- Bugs/issues (at least the biggest one)
- What you learned
- Next week plan

---

## 8) Suggested Commit Discipline (Solo-friendly)
- Use meaningful commit messages:
  - `infra: add docker compose for qdrant + minio`
  - `api: add receipts upload endpoint`
  - `ml: add receipt line grouping parser`
- Prefer small commits you can revert.

---

## 9) Backlog Policy
Backlog ideas go to:
- Backlog / Ideas section inside the weekly devlog
- Or (optional) `docs/backlog.md`

Do not expand scope mid-week unless it unblocks the main goal.

---

## 10) Weekly Plan Template (Optional)
If you create `docs/plans/YYYY-WW-plan.md`, use this template:

    # Plan — YYYY-WW
    ## Theme
    -
    ## Goals (3–6)
    - [ ]
    - [ ]
    - [ ]
    ## Tasks
    ### UI (Streamlit)
    - [ ]
    - [ ]
    ### API (FastAPI)
    - [ ]
    - [ ]
    ### Data/Infra
    - [ ]
    - [ ]
    ### ML/AI
    - [ ]
    - [ ]
    ## Demo checklist
    - [ ] docker compose up works
    - [ ] Happy path click-through works

---

## 11) How to Use This with `docs/roadmap.md`
- `docs/roadmap.md` is the long-term plan.
- `docs/devlogs/YYYY-WW.md` is the truth of what happened.
- Each week, copy tasks from roadmap → devlog goals.
