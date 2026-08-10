---
name: router
description: Route SDLC requests through clawdio's canonical skills and specialist agents. Use when the user asks to use clawdio, its router, or a multi-agent clawdio workflow.
---

# Router

This is a thin client adapter. It must not duplicate the router or specialist
prompts.

1. Read `../../references/dispatch-rules.md` in full and select the adapter for
   the active client.
2. Read `../../agents/router.md` in full. Treat it as the canonical routing and
   classification policy.
3. Follow that policy, translating its illustrative Claude tool syntax through
   the portability rules from step 1.
4. When dispatching a specialist from Codex, pass the resolved absolute path to
   the canonical `../../agents/<agent>.md` file. Require the subagent to read the
   dispatch rules first and the specialist file second. Do not paste or rewrite
   either prompt into the dispatch message.

Claude Code normally enters through the native `clawdio:router` agent. Codex
enters through this skill; both paths consume the same agent and workflow files.
