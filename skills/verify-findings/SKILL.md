---
name: verify-findings
description: Adversarially verifies specialist findings before they are presented or posted. Use when review, address-feedback, or triage agents return claims.
---

# Verify Findings

Specialist findings are claims, not facts. Before any Critical or Important finding is presented to the user or posted, dispatch one adversarial verifier per finding, tasked with refuting it. Nits pass through unverified -- not worth the tokens.

Read `../../references/dispatch-rules.md` before dispatching.

Two hard rules up front:

- Dispatch the logical `verifier` agent through the active client adapter.
- Verification fanout runs at the router main-loop level only. Do not nest it inside another specialist.

## Step 1: Fan out verifiers

One verifier agent per Critical/Important finding, all in parallel. Fresh context per finding -- no batching, no anchoring.

Each verifier prompt includes:

- The finding verbatim: severity, file:line, the claim, the suggested fix
- The repo and PR number (or the diff context if there is no PR)
- The instruction to REFUTE the finding, not to confirm it

For address-feedback claims, the finding to refute is "this fix addresses comment X" -- the verifier checks the diff actually resolves what the comment asked. For triage claims, the finding is the triage assessment (scope, reproducibility, labels).

## Step 2: Collect verdicts

| Verdict | Meaning | Handling |
|-|-|-|
| confirmed | Evidence the issue is real | Proceeds to presentation/posting |
| plausible | Could not refute, could not fully confirm | Proceeds to presentation/posting |
| refuted | Evidence it is wrong: unreachable path, existing guard or handling elsewhere, misread code, claimed line absent from diff | Filtered out, shown collapsed |

Line check: every verifier validates the finding's file:line against `gh api repos/{owner}/{repo}/pulls/{n}/files`. A finding whose line number cannot be verified is downgraded to a file + code snippet reference before posting -- never posted with a bad line number.

## Step 3: Output

Confirmed and plausible findings proceed unchanged. Refuted findings are never silently dropped -- they appear collapsed at the end of the report, one-line refutation each, so the filtering is auditable:

```
<details>
<summary>Filtered out by verification (2)</summary>

- ~~Critical: nil dereference in broker.go:42 (code-reviewer)~~ -- refuted: guarded by the err check at broker.go:38
- ~~Important: missing input validation in api.go:105 (security-auditor)~~ -- refuted: validated upstream in middleware.go:57
</details>
```

## Re-review rounds

Record refuted findings in the prior-review context that review-coordination Step 1.9 passes to specialists on round 2+, with the instruction not to re-raise them. Refuted findings do not resurrect.

## Anti-patterns

| Problem | Fix |
|-|-|
| Verifying Nits | Critical/Important only. Nits pass through. |
| One verifier for several findings | One verifier per finding. Fresh context avoids anchoring. |
| Silently dropping refuted findings | Show them collapsed with refutations. Always auditable. |
| Skipping verification because findings "look obviously right" | Obvious findings slip through. Always verify Critical/Important. |
| Running the fanout inside a subagent | Router main loop only. |
| Posting a finding with an unverified line number | Downgrade to file + snippet reference. |
| Bypassing the active client adapter | Follow `references/dispatch-rules.md`. |
