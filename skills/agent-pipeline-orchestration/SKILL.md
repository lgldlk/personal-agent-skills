---
name: agent-pipeline-orchestration
description: Manage complex coding or research work as a non-blocking multi-agent pipeline. Use when the user explicitly asks to use sub-agents, multiple agents, delegation, parallel work, a流水线式 workflow, or asks the main agent to manage/review while worker agents implement, review, QA, or map the next phase.
---

# Agent Pipeline Orchestration

## Overview

Run multi-agent work as a pipeline, not as a batch. Keep implementation, review, QA, and next-phase discovery moving in parallel while the main agent owns planning, boundaries, integration, and final verification. When workers are active, the main agent should not block idly, but should also avoid starting heavy overlapping work that makes returned worker output hard to integrate.

## Operating Model

Use the main agent as the tech lead:

- Define the target outcome and current phase.
- Split work into lanes with non-overlapping write scopes.
- Keep one immediate critical-path task local only when delegation would block progress.
- Spawn workers for bounded implementation, reviewers for independent checks, and mappers for next-phase discovery.
- While workers run, fill waiting time with small, reversible, low-conflict tasks.
- Wait for worker output when the next step depends on it, using explicit short wait windows instead of indefinite blocking.
- Review every returned change before treating it as accepted.
- Close completed agents promptly to free capacity.

## Lane Types

Keep 3-4 lanes active when capacity allows:

- Implementation lane: scoped code changes with a clear file ownership boundary.
- Review lane: read-only correctness, UX, security, or regression review.
- QA lane: tests, browser checks, visual inspection, or reproduction.
- Mapping lane: read-only discovery for the next feature slice.

Do not let all lanes write the same files. If two tasks need the same files, make one the owner and send follow-up findings to that same agent instead of spawning a competing writer.

## Pipeline Loop

1. State the lanes.
   Example: "Backend runtime, frontend shell, media actions, independent review."

2. Spawn the first lane set.
   Give each agent:
   - objective
   - allowed write paths
   - forbidden paths
   - tests to run
   - expected final report format

3. Wait briefly, then do light local work.
   After spawning workers, wait for the first useful result with a short window, usually 30-90 seconds for implementation or 10-30 seconds for review/mapping. If nothing returns, do light work that is easy to interrupt:
   - read or diff files outside worker write scopes
   - update progress docs or checklists
   - run already-known focused tests
   - inspect logs, grep for TODOs, or verify no forbidden paths changed
   - prepare the next small prompt
   - spawn a read-only reviewer or mapper if capacity is available

   Avoid heavy local work while workers own adjacent files. Heavy work includes broad refactors, large architecture changes, implementing the same feature slice, formatting the whole repo, or starting changes whose result will conflict with an active worker.

4. Check back before starting a new substantial task.
   If a worker is still running and the next useful local step is no longer light, wait again for a bounded interval. If the worker still does not return after repeated waits or errors, either narrow the scope and continue locally, or explicitly mark that lane blocked and move to a separate lane.

5. React to the first returned lane.
   When any agent returns:
   - read its summary
   - inspect the changed files
   - run targeted validation if cheap
   - send defects back to the same owning agent if it is still open
   - close the agent when accepted
   - immediately backfill the freed slot with the next non-conflicting task

6. Feed review findings into implementation lanes.
   If a reviewer finds a problem in files owned by an active worker, send the finding to that worker. Spawn a new worker only when the write scope is separate.

7. Keep capacity useful.
   If the agent limit is reached, close completed agents first. Prefer replacing a completed implementation lane with review/QA or next-phase mapping rather than waiting for every lane to finish.

8. Integrate and verify periodically.
   After a coherent slice lands, run focused tests. After several lanes land, run broader checks. Do not postpone all validation to the end.

## Waiting Policy

Use waiting intentionally:

- Wait when the next decision depends on an active worker's output.
- Wait after sending a worker defect back, so it has a chance to repair its own write scope.
- Wait before taking over an active worker's task, unless it has errored, timed out repeatedly, or the fix is tiny and clearly non-conflicting.
- Do not wait when there is a clear light task that improves integration without touching worker-owned files.

Suggested rhythm:

1. Spawn lanes.
2. Wait once for an early return.
3. Do one light local task.
4. Wait again.
5. Review any returned lane.
6. Only then start another implementation lane or take over a stalled lane.

This keeps the pipeline non-blocking without turning the main agent into a competing worker.

## Delegation Rules

- Delegate only when the user explicitly permits sub-agents or parallel agent work.
- Keep tasks concrete and self-contained.
- Prefer implementation tasks with disjoint write scopes over vague exploration.
- Use read-only mappers for uncertain next steps.
- Use reviewers to audit already-landed changes while implementation continues.
- Do not delegate the immediate blocking step if the main agent can finish it faster and safely.
- Do not duplicate work between main and sub-agents.
- Do not keep coding heavily while waiting for a worker that owns nearby files; prefer bounded waiting plus light integration tasks.

## Prompt Template

Use this structure for worker agents:

```text
You are a [role] sub-agent. The main agent owns final review.
Project: [path].
You are not alone in the workspace. Do not revert other changes.

Goal: [specific outcome].

Write scope:
- [allowed files/directories]

Do not modify:
- [forbidden files/directories]

Requirements:
1. [behavior]
2. [behavior]
3. [tests]

Final report:
- changed files
- behavior changes
- validation commands and results
- residual risks
```

Use this structure for review agents:

```text
Read-only review. Do not modify files.
Review scope: [files/directories].
Find correctness, regression, UX, security, or test gaps.
Report findings by severity with file paths and line numbers.
If no blocker, say so and list residual risks.
```

## Anti-Patterns

Avoid these patterns:

- Blocking on all agents before doing any new work.
- Never waiting for agents and immediately doing their work locally.
- Treating "do not block" as permission to start heavy overlapping changes.
- Spawning multiple writers for the same files.
- Waiting on a mapper before doing unrelated validation.
- Treating sub-agent output as accepted without inspecting changed files.
- Leaving completed agents open and hitting the agent limit.
- Running only implementation lanes with no review or QA lane.
- Sending broad prompts like "continue the feature" without ownership boundaries.

## Completion Criteria

Before final response:

- All active implementation agents are either completed and reviewed, or clearly left as pending work.
- Completed agents are closed.
- Relevant focused tests have run.
- Broader validation has run when the slice touched shared contracts.
- The user gets a concise status: completed lanes, validation, residual risks, and next lanes.
