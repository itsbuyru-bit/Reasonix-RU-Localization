# Using the AI localization skill

The repository includes a project skill for AI agents:

```text
.agents/skills/reasonix-localization/SKILL.md
```

It is an **instruction playbook**, not a language pack. It tells an AI how to
add BCP 47 locales, correct translations, build native patches, validate, test,
and open a PR safely.

## Reasonix

Reasonix discovers project skills under `.agents/skills/` automatically.

1. Open this repository as the workspace (or keep `.agents/skills/` in the
   workspace).
2. Invoke the skill:
   - `/reasonix-localization`, or
   - `run_skill("reasonix-localization")`.
3. If it is not listed, run `reasonix doctor capabilities --json` and check
   Settings → Skills; refresh/reopen the session after changing skill files.

No copying is required when the skill lives in this repository. The skill body
is loaded on demand and contains the safe workflows and verification matrix.

## Another AI agent

Copy the **whole folder**, not only the Markdown file:

```text
.agents/skills/reasonix-localization/
└── SKILL.md
```

Place it in the agent's skills directory, depending on the agent:

| Agent / convention | Destination |
|---|---|
| Reasonix project | `<workspace>/.agents/skills/reasonix-localization/` |
| Claude-style project | `<workspace>/.claude/skills/reasonix-localization/` |
| Agent with configurable skill roots | add `.agents/skills` as a skill root |
| Agent without skills support | paste `SKILL.md` into custom/system instructions |

Keep the frontmatter:

```yaml
---
name: reasonix-localization
description: Work with the Reasonix localization repo: BCP 47 language packs, native patches, validation, tests, and PRs.
runAs: inline
---
```

The body is self-contained. A generic agent that cannot load `SKILL.md` as a
skill can still use it as a long-lived system/custom instruction.

## What to check after installation

- The agent can name the repository workflows and the BCP 47 profile fields.
- It knows `ru-RU` is the reference locale, not the only language.
- It refuses to apply files to the installed app without an explicit request.
- It knows the validators: `validate_language_pack.py`, `check_docs.py`, tests.
- It uses a branch + PR, not a direct push to `main`.

## Skill or language pack?

| Thing | What it is |
|---|---|
| `.agents/skills/reasonix-localization/SKILL.md` | Instructions for the AI |
| `languages/<code>.json` + `locale/<code>.json` | A translation of Reasonix |

To add a language, give the AI the skill and ask it to follow Workflow A in
`SKILL.md` or [ADDING-A-LANGUAGE.md](ADDING-A-LANGUAGE.md).

## Updating

Pull the repository; the skill is versioned with the code. If you copied it to a
global/agent directory, copy the updated `SKILL.md` again.
