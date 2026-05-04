# Getting started: first session walkthrough

This file is the literal step by step guide for the first Claude Code session opened in this directory. **For any session after the first**, do not read this file; instead read `STATUS.md` to find the current phase and proceed from there.

## What you (Claude) should do, in order

### Step 1: orient

1. Read `CLAUDE.md` if you have not already (it should have auto loaded).
2. Read `STATUS.md` to confirm the next phase is Phase 0 (it should be on a fresh project).
3. Read `SPEC.md` end to end.
4. Read `agents/00-project-manager.md`.
5. Skim `docs/source/transcript.md` so you understand the source material the spec was built from.
6. List the contents of `design/` (the user's reference images; .webp files).
7. Read this file (you are here).

You now know: the project is a Black Scholes options pricer. There are 11 phases. Each phase has agent task lists. You, by default, are the Project Manager.

### Step 2: confirm with the user

Before any code is written, post a short orientation message to the user that names:

* What phase you are about to start (Phase 0).
* What the Phase 0 deliverables are.
* Which agents you plan to dispatch in parallel.
* The first concrete artifact you will produce (the implementation plan in `docs/plan.md`).

Wait for the user to ack before proceeding. The user may have new context (images placed in the folder, preference changes, etc.).

### Step 3: brainstorm and plan

Invoke the brainstorming skill to confirm Phase 0 scope:

```
Skill(skill="superpowers:brainstorming")
```

Then invoke writing plans to produce `docs/plan.md`:

```
Skill(skill="superpowers:writing-plans")
```

`docs/plan.md` should contain:

* A list of all 11 phases.
* For each phase: the agents involved, the deliverables, and the quality gates (QA, Security, Code Review, Risk where applicable).
* The current phase highlighted as "in flight".

### Step 4: dispatch Phase 0 agents

Phase 0 deliverables (per SPEC.md):

* Project Manager runs brainstorming and writes `docs/plan.md`. (Already done in Step 3.)
* UI/UX Designer drafts wireframes (output to `docs/design/wireframes.md`) and the design system. Reads visual references from `design/` at the project root.
* Security Engineer publishes the threat model and baseline.
* DevOps Engineer wires the local working directory into the existing GitHub repo `Mustafan4x/Vega`: runs `git init` in `/home/mustafa/src/vega/`, adds the repo as `origin`, pushes existing files as the first commit, then scaffolds `backend/` (uv) and `frontend/` (Vite plus React plus TypeScript plus Tailwind).
* Documentation Engineer writes the initial README and `docs/architecture.md`.

These can run in parallel. Use `superpowers:dispatching-parallel-agents` and dispatch each via the `Task` tool. Use the prompt template in `CLAUDE.md` under "How to dispatch a specialist agent".

Concrete example for the Security Engineer dispatch:

```
Task(
  description="Security: Phase 0 threat model",
  subagent_type="general-purpose",
  prompt="""You are the Security Engineer agent for the Vega project at /home/mustafa/src/vega.

Read these files first:
- /home/mustafa/src/vega/SPEC.md
- /home/mustafa/src/vega/CLAUDE.md
- /home/mustafa/src/vega/agents/08-security-engineer.md

Execute the Phase 0 tasks listed in your agent file. Specifically: write the threat model to /home/mustafa/src/vega/docs/security/threat-model.md, write the per phase hardening checklist to /home/mustafa/src/vega/docs/security/checklist.md, and stub out /home/mustafa/src/vega/docs/security/secrets.md.

Use the security-review skill via the Skill tool when forming the threat model. Stay strictly in the Security Engineer role.

When done, report:
1. Files written.
2. Any decisions you made that the PM should review (e.g., suggested CSP policy, rate limit thresholds, branch protection rules).
3. The next agent in the handoff chain per your agent file.
"""
)
```

Dispatch the UI/UX Designer, DevOps Engineer, and Documentation Engineer in the same session in parallel using the same template.

### Step 5: review handoffs

When each subagent reports back:

1. Read the files it wrote.
2. Verify the deliverables match the agent file's "Definition of done".
3. If yes, mark that part of Phase 0 done in `docs/plan.md`.
4. If no, re prompt the subagent with a specific correction (cite the agent file).

### Step 6: gate, check-in, and only then proceed

Before opening Phase 1:

* Confirm `docs/plan.md` reflects all Phase 0 deliverables as complete.
* Confirm the GitHub repo is initialized (DevOps Engineer task).
* Confirm the user has signed off on the wireframes (UI/UX Designer task).
* Confirm the threat model is published (Security Engineer task).
* Confirm `README.md` and `docs/architecture.md` exist (Documentation Engineer task).

When all five are true, **update `STATUS.md`** to flip Phase 0's status to `completed`, fill in "Completed on" with today's date, and set the "Next phase" line to "Phase 1 (likely bundled with Phase 2)". Then **run the mandatory check-in protocol from `CLAUDE.md` ("Pacing rule")**. Concretely, send the user a message like:

> Phase 0 is complete. Summary: implementation plan written, threat model published, wireframes accepted, repo wired into GitHub, frontend and backend scaffolded, README and architecture doc shipped.
>
> Before I open Phase 1, please tell me:
>
> 1. What is your Claude Max usage at right now?
> 2. Roughly how long until your next reset window?
> 3. Continue to Phase 1 now, pause until next window, or stop here?
>
> Phase 1 is the Python REPL for Black Scholes (small, ~30 percent of a window). I will likely bundle it with Phase 2 (FastAPI backend) so the next window fills cleanly. Estimated total cost for the bundle: roughly one full window.

Wait for the user's explicit answer. Do not auto advance, even in auto mode.

## What success looks like at the end of Phase 0

```
/home/mustafa/src/vega/
├── .git/                                      # Created by DevOps Engineer (git init)
├── .gitignore                                 # Created by DevOps Engineer
├── README.md                                  # Written by Documentation Engineer
├── CLAUDE.md                                  # Already exists
├── STATUS.md                                  # Already exists; PM flipped Phase 0 to "completed"
├── SPEC.md                                    # Already exists
├── GETTING-STARTED.md                         # Already exists
├── agents/                                    # Already exists, 17 files
├── design/                                    # Already exists, user reference .webp files
├── docs/
│   ├── plan.md                                # Written by you (PM) in Step 3
│   ├── setup-guide.md                         # Already exists
│   ├── source/transcript.md                   # Already exists
│   ├── architecture.md                        # Written by Documentation Engineer
│   ├── design/wireframes.md                   # Written by UI/UX Designer
│   ├── security/threat-model.md               # Written by Security Engineer
│   ├── security/checklist.md                  # Written by Security Engineer
│   └── security/secrets.md                    # Written by Security Engineer (stub)
├── backend/                                   # Initialized by DevOps Engineer with uv (empty FastAPI scaffold)
└── frontend/                                  # Initialized by DevOps Engineer with pnpm + Vite + React + TS + Tailwind (empty)
```

When this tree exists and every file's "Definition of done" is met, Phase 0 is complete and Phase 1 can begin.

## What to do on the second session and beyond

Ignore this file. Read `STATUS.md`. The "Next phase" line tells you exactly which phase to start. The user typically opens Claude Code and says "work on the next phase"; that maps directly to whatever `STATUS.md` says.

For mid phase resume (e.g., a paused phase from a prior window), read the "Resume notes" section of `STATUS.md` to find the last commit and the next concrete task.
