---
name: review-coordination
description: Coordinates multi-specialist PR review. Use when the router receives a pull request review request.
---

# Review Coordination

Coordinates multi-specialist PR review. Invoked by the router when a PR needs review.

Read `../../references/dispatch-rules.md` before dispatching or asking the user
for a decision. The router owns the review fanout on every client.

## Step 1: Classify the PR

Fetch the file list (NOT the diff, NOT the code):

```bash
gh pr view <number> --json files --jq '[.files[].path]'
```

Determine which specialists are needed:

```
Files in PR
├── *.go, controllers/, api/, internal/ → dispatch go-k8s-reviewer
├── *auth*, *oauth*, *oidc*, *token*, *policy* → dispatch auth-reviewer
├── *crypto*, *secret*, *key*, *.env*, *password* → dispatch security-auditor
└── Always → dispatch code-reviewer + test-verifier
```

**Non-negotiable:** code-reviewer AND test-verifier are ALWAYS dispatched. No exceptions for "trivial" changes, single-file PRs, config-only PRs, or documentation PRs. The test-verifier decides whether tests are needed, not the router. If you find yourself thinking "this is too simple for test verification", that is the exact moment you must dispatch test-verifier.

**Skip domain specialists only when ALL of these are true:**
- The diff is under 50 lines
- 2 files or fewer changed
- No files touch auth, payments, data access, secrets, or config/env

When all three hold, dispatch code-reviewer + test-verifier only. Otherwise, classify files and dispatch domain specialists as normal.

## Step 1.5: Check if the fix already landed on main

Many external PRs are weeks old. Before dispatching review agents, check if the code the PR changes still looks the same on main. If the fix already landed (via a different PR or a core team commit), close the PR as superseded.

```bash
# for each file the PR touches, check if the relevant code was already changed on main
for file in $(gh pr view <number> --json files --jq '.files[].path'); do
  git log --oneline -3 -- "$file"
done
```

If any recent commit on main addresses the same issue, close the PR with a comment crediting the author and pointing to the commit that fixed it.

## Step 1.7: Classify the changes

Before dispatching specialists, dispatch ONE read-only classifier through the active client adapter to fetch and classify the diff. You never read the diff yourself.

The classifier's prompt:
- Fetch the diff via `gh pr diff <number>` or `gh api repos/{owner}/{repo}/pulls/{number}/files`
- Classify each changed file into exactly one bucket, with a one-line reason per file:

| Bucket | Contains |
|-|-|
| behaviour | logic, control flow, state, error handling, API behaviour |
| types-mechanical | type annotations, signatures, renames, imports, formatting, generated code |
| mixed | both; note which hunks are behaviour |
| tests-docs | test and documentation changes |

Wait for the classifier to return before dispatching specialists -- this step is sequential, then Step 2 runs in parallel. The classification feeds two places:
- Each specialist dispatch prompt (Step 2)
- The internal review summary used to weight and verify findings (Step 3)

## Step 1.9: Gather prior review context (round 2+ only)

On re-review (when Step 6 loops back with a round number > 1), fetch prior review context before dispatching agents. Skip this step entirely on the first review round.

```bash
# fetch prior review verdicts (state, author, body)
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '[.[] | {state, user: .user.login, body}]'

# fetch prior inline review comments (path, line, body, author)
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '[.[] | {path, line: .original_line, user: .user.login, body, created_at}]'
```

Assemble a prior-review summary containing:
- **Prior verdicts**: which reviewers posted, what verdict (APPROVED, CHANGES_REQUESTED, COMMENTED), and the verdict body
- **Prior findings**: the inline comments grouped by file, with severity labels if present
- **Refuted findings**: findings filtered out by verification (Step 3.5) in earlier rounds, each with its one-line refutation. Source these from the prior round's session context; they are not author-facing feedback.

This summary is passed to agents in Step 2.

## Step 2: Dispatch in parallel

Spawn all needed specialists simultaneously through the active client adapter.

Pass each agent:
- The PR number
- The full file list
- The change classification from Step 1.7, with the instruction to weight attention to behaviour and mixed files
- Instructions to read the diff via `gh pr diff <number>` and the PR description via `gh pr view <number>`

**On round 2+, also pass each agent:**
- The round number (e.g. "This is review round 2")
- The prior-review summary from Step 1.9
- These instructions: "Prior review findings are listed below. Verify that flagged issues were addressed. Do not re-flag findings that have been resolved. Findings listed as refuted were checked by an adversarial verifier and found to be false positives -- do not re-raise them. Only raise genuinely new issues not covered by prior rounds."

Example: for a Go PR with auth changes, dispatch these four logical agents in parallel:
- `code-reviewer`
- `test-verifier`
- `go-k8s-reviewer`
- `auth-reviewer`

## Step 3: Collect, merge, and decide

When all specialists return, synthesise their findings into a single assessment. Do NOT just list reports -- merge them across these axes:

1. **Code quality** -- aggregate Critical/Important findings from code-reviewer and domain specialists. Resolve duplicates.
2. **Test coverage** -- pull from test-verifier. Flag gaps in acceptance criteria coverage.
3. **Security** -- promote any Critical findings from security-auditor (if dispatched) to blockers.
4. **Performance** -- pull from code-reviewer's performance findings or domain specialists.

Then produce an internal verdict and a short author-facing review body.

**All findings go as inline comments on the diff.** Do not duplicate findings in the body. Nits are excluded unless the user explicitly asked for them.

```
Thanks for [specific contribution or earlier revisions, when warranted]. A few [plain-language summary] remain; happy to re-review and look to merge once these are addressed.
```

If any specialist returned a Critical finding, the default verdict is CHANGES REQUESTED.

## Step 3.5: Verify findings

Before presenting or posting anything, invoke `clawdio:verify-findings` on the merged Critical and Important findings. Nits pass through unverified. The skill fans out one verifier agent per finding (router main loop, in parallel) and returns a verdict for each.

- **Confirmed** and **plausible** findings proceed to Step 4 unchanged.
- **Refuted** findings stay in the internal draft with a one-line refutation so the user can audit what was filtered. Do not post them to the author.
- Findings whose file:line could not be validated against the diff are downgraded to file + code snippet references before posting.

## Step 4: Post to GitHub

Present the draft to the user. Follow the applicable project instructions (`AGENTS.md`, `CLAUDE.md`, or both): focused inline comments, a terse human review body, and no duplication.

Use the user-decision mechanism from the portability rules to present the full draft with options: "Post as-is", "Edit first", "Don't post". Do not post without explicit approval.

Once approved, post using the protocol below.

### Posting review findings

Get the head commit SHA first:

```bash
COMMIT_SHA=$(gh api repos/{owner}/{repo}/pulls/{number} --jq '.head.sha')
```

Post via `gh api` with the reviews endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --method POST --input - <<'EOF'
{
  "commit_id": "<commit_sha>",
  "event": "REQUEST_CHANGES",
  "body": "Thanks for working through the earlier feedback. A few error-path issues remain; happy to re-review and look to merge once these are addressed.",
  "comments": [
    {
      "path": "internal/broker/broker.go",
      "line": 42,
      "body": "This can dereference a nil value on the error path. Could we guard `err != nil` before accessing it?"
    }
  ]
}
EOF
```

Rules:
- `event`: `"REQUEST_CHANGES"` when verdict is CHANGES REQUESTED or BLOCKED. `"COMMENT"` when APPROVE.
- `body`: one or two short sentences. Thank the author only for something specific, summarise what remains without listing findings, and state the next step. Keep findings outside the diff in the user-facing draft for separate handling; do not make the review body dense to work around GitHub's inline-comment restriction.
- `comments`: array of inline findings. Each needs `path`, `line` (line number in the NEW file from the diff hunk headers), and `body`. State the observed behaviour or risk, then offer a practical suggestion. Prefer "Could we ...?" where the implementation choice belongs to the author. Omit severity labels unless repository instructions require them. No nits unless user asked.
- `commit_id`: the head SHA fetched above. Required.

## Step 5: Suggest next action

After posting, if the verdict is CHANGES REQUESTED or BLOCKED, offer next steps through the active user-decision mechanism:

- "Address the feedback" → dispatch the **address-feedback** agent (NOT the router -- the router never fixes code)
- "Merge anyway" → invoke `clawdio:merge-gate`
- "Done for now" → stop

If the verdict is APPROVE, offer:
- "Merge" → invoke `clawdio:merge-gate`
- "Done for now" → stop

The address-feedback agent reads the review comments, categorises them, fixes what it can, and reports what needs your input. The router NEVER addresses feedback itself.

## Step 6: After address-feedback completes

When the address-feedback agent finishes, offer next steps through the active user-decision mechanism:

- "Re-review" → run review coordination again (Step 1) with the round number incremented (first review = round 1, so first re-review = round 2, etc.). The round number triggers Step 1.9 to gather prior context before dispatch.
- "Merge" → invoke `clawdio:merge-gate`
- "What's on" → invoke `clawdio:next` to check for other work
