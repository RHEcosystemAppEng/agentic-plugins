# CodeRabbit PR commands

CodeRabbit auto-reviews pull requests using [`.coderabbit.yaml`](../.coderabbit.yaml).
You can also drive it from a **PR comment**.

> Commands are **not** slash commands like `/review`.
> Post them as: `@coderabbitai <command>`

Official reference: [Review commands](https://docs.coderabbit.ai/reference/review-commands)

## How to post a command

1. Open the pull request on GitHub
2. Add a **new top-level comment** (not a reply inside a thread, unless the command says otherwise)
3. Put the command alone on its line, for example:

   ```text
   @coderabbitai review
   ```

4. One command per comment
5. Do not wrap the command in a code fence if you want it to run
6. Free-form chat also works for org members, for example: `@coderabbitai why did you flag this?`

In this repo, **non-org members cannot chat** with the bot (`allow_non_org_members: false`).
Org members / collaborators can.

## Commands developers use most

| Comment | What it does |
| --- | --- |
| `@coderabbitai review` | Incremental review of commits since the last CodeRabbit review |
| `@coderabbitai full review` | Re-review the whole PR from scratch |
| `@coderabbitai summary` | Regenerate the PR summary |
| `@coderabbitai pause` | Stop automatic reviews on this PR |
| `@coderabbitai resume` | Resume automatic reviews after a pause |
| `@coderabbitai help` | List commands available on this PR |
| `@coderabbitai configuration` | Show the resolved config (and where each setting came from) |
| `@coderabbitai rate limit` | Show whether another review is available now |
| `@coderabbitai run pre-merge checks` | Re-run configured pre-merge checks (description warning, etc.) |

## Fix / follow-up commands

| Comment | What it does |
| --- | --- |
| `@coderabbitai resolve` | Resolve all CodeRabbit review threads on the PR. **Does not verify** that findings were fixed — it only closes discussion threads |
| `@coderabbitai fix comments` | Attempt to fix unresolved CodeRabbit findings and commit to the branch |
| `@coderabbitai local commit` | Commit changes CodeRabbit proposed in a comment. **Must be posted as a reply** to that CodeRabbit comment (not as a top-level PR comment) |
| `@coderabbitai autofix` | Keep fixing CodeRabbit findings / required CI / merge conflicts on the PR |
| `@coderabbitai generate sequence diagram` | Post a sequence diagram of the PR changes |
| `@coderabbitai generate unit tests` | Generate unit tests for changed code (plan-dependent) |
| `@coderabbitai simplify` | Suggest/apply simplifications for changed code (plan-dependent) |

## Repo-specific notes (agentic-plugins)

- **Auto-review is on** for every push (`auto_pause_after_reviewed_commits: 0`)
- **Approvals are off** (`auto_approvals.enabled: false`): `@coderabbitai approve` will not approve the PR. Human / CODEOWNERS approval is still required.
- Skip auto-review with a `hold` label, a WIP title (`wip:` / `[WIP]`), or a GitHub Draft PR
- Reviews stay short and contract-focused (skills, `mcps.json`, Compass, `AGENTS.md`, secrets, `**/uv.lock`)
- CodeRabbit does **not** replace `make validate` or required human review

## Suggested workflow

1. Open the PR and fill [`.github/pull_request_template.md`](pull_request_template.md)
2. Let the first auto-review finish
3. Address findings (or ask in chat: `@coderabbitai explain this finding`)
4. After a batch of fixes, run `@coderabbitai review` or `@coderabbitai full review`
5. If reviews were paused, run `@coderabbitai resume`
6. Ask a CODEOWNER for the human approval required to merge

## Related docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) — contribution flow and CodeRabbit overview
- [`.coderabbit.yaml`](../.coderabbit.yaml) — review policy
- [CodeRabbit command reference](https://docs.coderabbit.ai/reference/review-commands)
