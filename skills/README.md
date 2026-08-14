# README

This directory contains skills that can be imported into AI assistants to conduct AIRBDS assessments.

Skill versions being tested are in `testing/`
Skill versions under development are in `development/`

The **production** skill is not a directory here: it is published to the
publication repository, [AIBIO-UK/airbds-core][core], as
[`skills/airbds-assessment-skill.zip`][prod-zip]. It is the `testing` build,
with its release channel rewritten, promoted by a maintainer — so it exists in
exactly one place and cannot drift from a copy kept here. Install that one
unless you specifically want the staging build.

Gavin's personal variant in [`GF/`](GF/README.md) is **dormant**: it is pinned to
AIRBDS metric v0.3, is not updated on a metric release, and should not be used
for an assessment.

We recommend you use the most capable model you have to perform the assessment.

# Installation instructions

Below there are some instructions for using the skills with different AI assistant providers (e.g. Google, Anthropic).

Other instructions to follow. Pull requests containing instructions or code for getting these skills to work with other assistants very welcome.

When a skill is installed the assistant will automtically pick it up when relevant. So to perform an assessment you can prompt something like "Please perform an AIRBDS assessment on <dataset-url>", e.g. "Please perform an AIRBDS assessment on https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7"

## Claude Web (claude.ai) and Claude Desktop

### Before you start

You need **Code execution and file creation** turned on: 

- **Free, Pro, Max:** go to [Settings → Capabilities](https://claude.ai/settings/capabilities) and toggle it on. 
- **Team:** enabled by default.
- **Enterprise:** an Owner must enable both **Code execution and file creation** and **Skills** in [Organization settings → Skills](https://claude.ai/admin-settings/skills) first.

### Install the skill

1. [Download the skill][prod-zip]
2. Go to [Customize → Skills](https://claude.ai/customize/skills).
3. Click the **+** button, then **Create skill → Upload a skill**.
4. Upload the skill.

The skill appears in your Skills list, enabled by default.

Prefer to try the staging build instead? Download
[the `testing` release](https://github.com/AIBIO-UK/airbds-dev/releases/download/assessment-skill-testing/airbds-assessment-skill-testing.zip)
and install it the same way. It is the same bundle, on the `testing` release
channel — so it checks for updates against `testing` rather than `production`,
and may be ahead of what production offers.

### Reference

Anthropic's full guide: <https://support.claude.com/en/articles/12512180-use-skills-in-claude>

## Claude Code

```
/plugin marketplace add AIBIO-UK/airbds-dev
/plugin install airbds-assessment@airbds-marketplace
```

The marketplace is defined in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json);
`airbds-marketplace` is its `name`, which is what `/plugin install` matches on — not the
repository name.

## Gemini

> ⚠️ **Gemini support is paused for now.**
>
> Gemini can only run the skill as a 'Gem', which cannot be built directly from
> this repository — a Gem has to be created and shared manually. That makes it
> painful to keep in sync with the skill and impossible to test automatically
> (see [`testing/ISSUES.md`](testing/ISSUES.md)), so we've paused it rather than
> ship a Gem that quietly drifts out of date.
>
> We plan to bring Gemini support back once the AIRBDS assessment reaches v1.0
> and the skill workflow has stabilised. In the meantime, please use Claude
> (Web, Desktop, or Code) below.

---

[core]: https://github.com/AIBIO-UK/airbds-core
[prod-zip]: https://github.com/AIBIO-UK/airbds-core/raw/main/skills/airbds-assessment-skill.zip

> **Maintaining the skills?** Release channels, the `versions.json` update
> manifest, and how to propagate a metric version bump are documented in
> [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md). How a skill is put together —
> what `SKILL.md` and the bundled `assets/` do, and why the metric is carried as
> data rather than restated as prose — is in [`docs/DESIGN.md`](docs/DESIGN.md).
