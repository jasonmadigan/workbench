# Dispatch Rules

Cross-cutting rules for agents and skills that dispatch subagents or interact with users.

## Agent dispatch

Never pass `name` to the Agent tool. Named agents spawn into mailbox mode and sit idle. Use `subagent_type` and track by the returned `agentId`.

## User decisions

Every user decision point uses `AskUserQuestion` with clickable options (2-4 concrete choices). Never present a decision as plain text expecting the user to type. Applies to: post/edit/don't-post, draft/ready, next-step suggestions, merge confirmations.

## Skill loading

Agents that load skills at startup use one line:

```
1. **Load skills:** `agent-skills:x`, `agent-skills:y` — invoke all before proceeding.
```
