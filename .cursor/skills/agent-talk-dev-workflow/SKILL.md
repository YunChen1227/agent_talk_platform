---
name: agent-talk-dev-workflow
description: >-
  Enforces design-first development workflow for the AgentMatch Platform
  (agent_talk_platform). Use when writing, modifying, or implementing any
  feature code in the agent_talk_platform project. Ensures DESIGN docs are
  updated before code changes, and code stays consistent with design.
---

# AgentMatch Platform - Design-First Development Workflow

This skill enforces a strict **Design → Diff → Code** workflow: every code
change must start from the design document, then verify alignment, then
implement.

## Project Structure Overview

```
agent_talk_platform/
├── design/                        # Design docs (source of truth)
│   ├── DESIGN.md                  # Core design overview
│   ├── DESIGN-USER.md             # User module
│   ├── DESIGN-AGENT.md            # Agent module
│   ├── DESIGN-SKILL.md            # Skill module
│   ├── DESIGN-USERSHOP.md         # UserShop module
│   ├── DESIGN-MATCHER.md          # Matcher engine
│   ├── DESIGN-SESSION.md          # Session sandbox
│   ├── DESIGN-JUDGE.md            # Judge system
│   ├── DESIGN-ORCHESTRATOR.md     # Orchestrator
│   ├── DESIGN-LLM.md             # LLM service
│   ├── DESIGN-API.md             # API endpoints
│   ├── DESIGN-FRONTEND.md        # Frontend overview
│   ├── DESIGN-PAGE-LOGIN.md      # Page: Login
│   ├── DESIGN-PAGE-DASHBOARD.md  # Page: Dashboard
│   ├── DESIGN-PAGE-PLAZA.md      # Page: Agent Plaza
│   ├── DESIGN-PAGE-AGENT.md      # Page: Agent create/edit
│   ├── DESIGN-PAGE-SHOP.md       # Page: User Shop
│   └── DESIGN-PAGE-PROFILE.md    # Page: User Profile
├── backend/                       # FastAPI backend
│   └── app/
│       ├── api/                   # Route handlers
│       ├── models/                # Data models
│       ├── schemas/               # Pydantic schemas
│       ├── services/              # Business logic
│       ├── repositories/          # Data access layer
│       └── agent/                 # Agent core
└── frontend/                      # Next.js 14 frontend
    ├── app/                       # Page routes
    ├── components/                # Shared components
    └── lib/                       # API client
```

## Design-to-Code Mapping

Use this table to find the relevant DESIGN doc(s) for any code change:

| Code Area | Primary Design Doc | Secondary |
|---|---|---|
| `backend/app/models/user.py`, `schemas/user.py`, `services/user_service.py`, `api/auth.py` | DESIGN-USER.md | DESIGN-API.md |
| `backend/app/models/agent.py`, `schemas/agent.py`, `api/agents.py`, `agent/` | DESIGN-AGENT.md | DESIGN-API.md |
| `backend/app/models/skill.py`, `schemas/skill.py`, `api/skill.py` | DESIGN-SKILL.md | DESIGN-API.md |
| `backend/app/models/product.py`, `schemas/product.py`, `services/shop_service.py`, `api/shop.py` | DESIGN-USERSHOP.md | DESIGN-API.md |
| `backend/app/services/matcher_service.py` | DESIGN-MATCHER.md | DESIGN-ORCHESTRATOR.md |
| `backend/app/models/session.py`, `schemas/session.py`, `api/sessions.py` | DESIGN-SESSION.md | DESIGN-API.md |
| `backend/app/services/judge_service.py` | DESIGN-JUDGE.md | DESIGN-ORCHESTRATOR.md |
| `backend/app/services/orchestrator.py` | DESIGN-ORCHESTRATOR.md | DESIGN.md |
| `backend/app/services/llm.py` | DESIGN-LLM.md | — |
| `backend/app/models/media.py`, `schemas/media.py`, `services/media_service.py`, `api/media.py` | DESIGN-USER.md (media section) | DESIGN-API.md |
| `frontend/app/login/` | DESIGN-PAGE-LOGIN.md | DESIGN-FRONTEND.md |
| `frontend/app/page.tsx` (dashboard) | DESIGN-PAGE-DASHBOARD.md | DESIGN-FRONTEND.md |
| `frontend/app/plaza/` | DESIGN-PAGE-PLAZA.md | DESIGN-FRONTEND.md |
| `frontend/app/agent/` | DESIGN-PAGE-AGENT.md | DESIGN-FRONTEND.md |
| `frontend/app/shop/` | DESIGN-PAGE-SHOP.md | DESIGN-FRONTEND.md |
| `frontend/app/profile/` | DESIGN-PAGE-PROFILE.md | DESIGN-FRONTEND.md |
| `frontend/lib/api.ts` | DESIGN-API.md | DESIGN-FRONTEND.md |

## Workflow (Mandatory 3 Steps)

When the user asks to implement, modify, or fix any feature, follow these
three steps **in order**. Do NOT skip steps.

### Step 1: Update Design Docs

1. Identify which DESIGN doc(s) relate to the requested change using the
   mapping table above.
2. Read the relevant DESIGN doc(s) in full.
3. If the user's request introduces new behavior, new fields, new endpoints,
   or changes existing definitions:
   - Propose the design changes to the user and get confirmation.
   - Update the DESIGN doc(s) to reflect the new/changed design.
   - Keep the doc style consistent: same formatting, same level of detail.
4. If the DESIGN doc already covers the requested behavior accurately,
   explicitly state "Design docs are already up to date" and proceed.

### Step 2: Diff Design vs Code

1. Read the relevant source code files (models, schemas, services, API
   routes, frontend pages) that correspond to the DESIGN doc(s).
2. Compare the DESIGN doc definitions against the current code. Check for:
   - **Missing implementations**: fields/endpoints/logic described in DESIGN
     but absent in code.
   - **Extra implementations**: code that exists but is not documented in
     DESIGN (flag for review).
   - **Mismatches**: field names, types, enum values, API paths, request/
     response shapes, UI components that differ between DESIGN and code.
3. Produce a concise diff summary listing each discrepancy. Format:

```
Design vs Code Diff:
- [MISSING] DESIGN-AGENT.md defines field `demand_summary` but agent model lacks it
- [MISMATCH] DESIGN-API.md says POST /agents returns AgentDetail, code returns AgentSummary
- [EXTRA] Code has `agent.priority` field not documented in any DESIGN doc
```

4. If there are no discrepancies beyond the user's requested change, state
   "No additional discrepancies found."

### Step 3: Implement Code Changes

1. Based on the updated DESIGN docs (Step 1) and the diff (Step 2),
   implement all necessary code changes.
2. Address both the user's original request AND any discrepancies found
   in Step 2 (after confirming with the user if the discrepancies are
   non-trivial).
3. Ensure the final code is fully consistent with the DESIGN docs.
4. After making changes, verify by re-reading key files to confirm
   alignment.

## Important Rules

- **DESIGN docs are the source of truth.** Code must match DESIGN, not the
  other way around. If code and DESIGN disagree, update code (unless the
  user explicitly requests a design change).
- **Never skip Step 1.** Even for "small fixes", check the DESIGN doc first.
  The fix might reveal a design gap.
- **Ask before large design changes.** If the user's request implies
  significant design modifications (new modules, changed data models,
  altered business flows), present the proposed DESIGN changes and get
  user confirmation before proceeding.
- **Keep diffs concise.** The Step 2 diff summary is for awareness, not
  for exhaustive documentation. Focus on actionable discrepancies.
- **One feature at a time.** If the user asks for multiple unrelated
  changes, process each through the full 3-step workflow sequentially.
