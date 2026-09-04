# README

This directory contains the development and testing channels for skills that can be imported into AI assistants to conduct AIRBDS assessments.

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

## Installation instructions

[Development channel skill][dev-zip]

[Testing channel skill][test-zip]

With many assistants (e.g. Claude Code, Hermes Agent) all you need to do is:

1. Download one of the channel skill zips listed above.
2. Give the zip to the assistant — attach it to a message, or point the assistant at the downloaded file — and ask it to install the skill.

In some cases, such as for Claude Web, the assistant can't do this directly but will give you the instructions for a manual installation when you ask it to install the skill zip.

Some assistants, such as Gemini, do not support the agentskills.io standard. They may have alternative formats - Gemini, for example, has 'Gems'. We do not publish the skill in those formats.

When a skill is installed the assistant will automtically pick it up when relevant. So to perform an assessment you can prompt something like "Please perform an AIRBDS assessment on <dataset-url>", e.g. "Please perform an AIRBDS assessment on https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7"

Some platform-specific installation instructions are listed below if you need to do this manually rather than be instructing the agents. Pull requests for more instructions for other platforms are welcome!

### Claude Web (claude.ai) and Claude Desktop

#### Before you start

You need **Code execution and file creation** turned on: 

- **Free, Pro, Max:** go to [Settings → Capabilities](https://claude.ai/settings/capabilities) and toggle it on. 
- **Team:** enabled by default.
- **Enterprise:** an Owner must enable both **Code execution and file creation** and **Skills** in [Organization settings → Skills](https://claude.ai/admin-settings/skills) first.

#### Install the skill

1. Download the appropriate channel skill from the links above.
2. Go to [Customize → Skills](https://claude.ai/customize/skills).
3. Click the **+** button, then **Create skill → Upload a skill**.
4. Upload the skill.

The skill appears in your Skills list, enabled by default.

#### Reference

Anthropic's full guide: <https://support.claude.com/en/articles/12512180-use-skills-in-claude>

### Claude Code

Execute these CLI commands.

```
/plugin marketplace add AIBIO-UK/airbds-dev
/plugin install airbds-assessment@airbds-marketplace
```

The marketplace is defined in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json);
`airbds-marketplace` is its `name`, which is what `/plugin install` matches on — not the
repository name.

---

[core]: https://github.com/AIBIO-UK/airbds-core
[dev-zip]: https://github.com/AIBIO-UK/airbds-dev/releases/download/assessment-skill-development/airbds-assessment-skill-development.zip
[test-zip]: https://github.com/AIBIO-UK/airbds-dev/releases/download/assessment-skill-testing/airbds-assessment-skill-testing.zip
[prod-zip]: https://github.com/AIBIO-UK/airbds-core/raw/main/skills/airbds-assessment-skill.zip

> **Maintaining the skills?** Release channels, the `versions.json` update
> manifest, and how to propagate a metric version bump are documented in
> [`docs/MAINTAINING.md`](docs/MAINTAINING.md). How a skill is put together —
> what `SKILL.md` and the bundled `assets/` do, and why the metric is carried as
> data rather than restated as prose — is in [`docs/DESIGN.md`](docs/DESIGN.md).
