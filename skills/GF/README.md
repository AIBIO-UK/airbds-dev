# GF Personal Skills

This directory contains personal/experimental skill variants authored by Gavin Farrell (GF),
maintained in parallel with the team's `testing/` skills for individual experimentation.

This variant collects reviewer metadata (name, initials, ORCID, affiliation, review number) before the assessment, then writes the completed review to `reviews/<accession>_<INITIALS>_<n>.yaml` — ready for automated scoring by the `review-check` workflow.

**These skills are not production-ready and have not been agreed with the team.**
They exist for personal testing and as a proof-of-concept for improvements to discuss.

## Key differences from `testing/`

| Feature | `testing/` skill | `GF/` skill |
|---------|-----------------|-------------|
| Output | Assessment table in chat only | Assessment table + YAML review file written to `reviews/` |
| Reviewer metadata | Not collected | Collected at start (name, initials, ORCID, affiliation, n) |
| Works in Claude Code | ✅ | ✅ |
| Works in Claude Web | ✅ | ✅ (requires Code execution + file creation) |

## Skills

- [`GF-airbds-assessment-skill/`](GF-airbds-assessment-skill/) — YAML-based assessment that writes directly to `reviews/`

## Installation (Claude Code)

The GF skills are not registered in the marketplace. To use in Claude Code, either:

1. Install via local path (when supported), or
2. Read the SKILL.md and apply the instructions inline in a Claude Code session.

For now, the simplest approach is inline: open Claude Code in the repo directory and prompt:
> "Please read skills/GF/GF-airbds-assessment-skill/SKILL.md and follow its instructions to assess [dataset URL]"

## Installation (Claude Web) with Code execution + file creation

Follow the same **Enable Code execution and file creation** step as in `skills/README.md`, then prompt:

```
Please read the SKILL.md I'm about to paste and follow its instructions…
```

