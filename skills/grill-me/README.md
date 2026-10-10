# Grill Me

A read-only interview skill for pressure-testing ideas, plans, product decisions, architectures, and research proposals before implementation.

Grill Me asks exactly one consequential question at a time, recommends a position with its main trade-off, tracks facts and assumptions, reopens contradictory decisions, stress-tests failure modes, and converges on a copyable decision brief.

> 中文简介：通过逐题追问、事实核验和压力测试，将想法收敛为可执行的决策简报。

## Core behavior

- Prioritizes questions by impact, uncertainty, dependency centrality, and reversal cost.
- Resolves discoverable facts through read-only inspection before asking the user.
- Separates verified facts, assumptions, decisions, risks, and unresolved questions.
- Detects contradictions and reopens decisions that depend on invalidated premises.
- Stops when remaining uncertainty is local, inexpensive, or reversible.
- Never edits files, sends messages, deploys, purchases, schedules, or otherwise implements the plan while the skill is active.

The canonical portable skill is [`SKILL.md`](./SKILL.md). The Claude Code variant is [`claude-code/SKILL.md`](./claude-code/SKILL.md); it adds explicit command metadata while keeping the interview body identical.

## Install

### Codex and Agent Skills-compatible clients

This skill is maintained within the Agent workspace at `~/.agents/skills/grill-me`.
For installed hosts, use the repository's [synchronization workflow](../README.md#宿主同步):

```bash
python3 ~/.agents/skills/scripts/sync.py
```

For a project-local copy:

```bash
mkdir -p "$REPO_ROOT/.agents/skills/grill-me"
cp ~/.agents/skills/grill-me/SKILL.md "$REPO_ROOT/.agents/skills/grill-me/SKILL.md"
cp -R ~/.agents/skills/grill-me/evals "$REPO_ROOT/.agents/skills/grill-me/evals"
```

Then explicitly select or mention the `grill-me` skill with the idea or decision to examine.

### Claude Code

The canonical skill can be linked through the same synchronization workflow.
The [Claude Code variant](claude-code/SKILL.md) provides explicit command metadata;
if that variant is needed, install it into a separate host-owned skill directory
after inspecting existing files and links. Preserve the managed canonical source
when choosing the destination.

Invoke it explicitly:

```text
/grill-me your idea, plan, design, or decision
```

## Interaction contract

Each interview turn contains one decision question, a concrete recommendation, and the principal trade-off. The supported control replies are:

- `accept` — record the recommendation as the decision.
- `change: ...` — record an alternative and update dependent decisions.
- `unknown` — choose a reversible default or define the cheapest useful validation step.
- `skip` — defer the decision and record the consequence when material.
- `summary` — show the current ledger, then continue with one next question.
- `stop` — produce the best available decision brief and end the session.

Final approval closes the interview. It never authorizes implementation; implementation requires a separate explicit request after the skill ends.

## Repository layout

```text
.
├── SKILL.md                         # Canonical portable skill
├── evals/
│   ├── eval_queries.json            # Trigger and non-trigger cases
│   └── evals.json                   # Output-quality cases
├── claude-code/
│   ├── SKILL.md                     # Explicit /grill-me command variant
│   └── evals/                       # Matching evaluation data
├── scripts/validate.py              # Dependency-free repository checks
└── .github/workflows/validate.yml   # CI validation
```

## Validate

```bash
python3 ~/.agents/skills/grill-me/scripts/validate.py
```

The validator checks frontmatter invariants, version consistency, identical interview bodies across variants, valid evaluation schemas, unique evaluation IDs, and synchronized evaluation data.

## Version

Current skill version: `2.0.0`.

## License

[MIT](./LICENSE)
