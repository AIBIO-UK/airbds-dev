# README

This directory contains skills that can be imported into AI assistants to conduct AIRBDS assessments.

Skill versions being tested are in `testing/`
Skill versions under development are in `development/`

There are no production skills yet.

## Version manifest (`versions.json`)

`versions.json` is the source of truth for the **current** assessment skill on
each channel. It is served over GitHub raw at
<https://raw.githubusercontent.com/AIBIO-UK/airbds-metric/main/skills/versions.json>.
Each entry under `channels` records the `metric_version` that channel's current
skill assesses against, a `skill_version`, and a `skill_update_url`.

At start-up an assessment skill makes a best-effort fetch of this manifest and
compares the manifest's `metric_version` for **its own channel only** against
the `metric_version` declared in its own frontmatter. If the manifest is
strictly newer, the skill pauses and **asks the user** whether to proceed with
the older bundled metric or stop and update to the newer skill first — it does
not start the assessment until they choose. If the fetch fails it is silently
skipped (a failed fetch never blocks an assessment). A skill never looks at
other channels — so a `testing` skill is **not** nudged when `development` moves
ahead.

**Maintenance:** bump a channel's `metric_version` here whenever that channel's
released skill starts targeting a new AIRBDS metric version (i.e. whenever you
update the skill's bundled `templates/airbds_metric_v*.yaml` and its
`metric_version` frontmatter). Keep this file in step with the per-channel skill
frontmatter, otherwise the update check goes stale.

For information on Gavin's skill under test please see `GF/README.md`

We recommend you use the most capable model you have to perform the assessment.

# Installation instructions

Below there are some instructions for using the skills with different AI assistant providers (e.g. Google, Anthropic).

Other instructions to follow. Pull requests containing instructions or code for getting these skills to work with other assistants very welcome.

When a skill is installed the assistant will automtically pick it up when relevant. So to perform an assessment you can prompt something like "Please perform an AIRBDS assessment on <dataset-url>", e.g. "Please perform an AIRBDS assessment on https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7"

## Gemini

For Gemini, the skill has to be run as a 'Gem'. This either has to be done:

- By going to [this shared Google Gem URL](https://gemini.google.com/gem/14YUoz1uJqOSO0YA0jty4vrux3FoU_dBU?usp=sharing) or
- Manually from this repository, using the contents of the SKILL.md and uploading the template file

You will need to have already registered for Google Gemini for the link to work. We strongly recommend that you use the latest Pro model to run the assessment.

## Claude Web (claude.ai) and Claude Desktop

### Before you start

You need **Code execution and file creation** turned on: 

- **Free, Pro, Max:** go to [Settings → Capabilities](https://claude.ai/settings/capabilities) and toggle it on. 
- **Team:** enabled by default.
- **Enterprise:** an Owner must enable both **Code execution and file creation** and **Skills** in [Organization settings → Skills](https://claude.ai/admin-settings/skills) first.

### Install the skill

1. [Download the skill](https://github.com/AIBIO-UK/airbds-metric/releases/download/assessment-skill-testing/airbds-assessment-skill.zip)
2. Go to [Customize → Skills](https://claude.ai/customize/skills).
3. Click the **+** button, then **Create skill → Upload a skill**.
4. Upload the skill.

The skill appears in your Skills list, enabled by default.

### Reference

Anthropic's full guide: <https://support.claude.com/en/articles/12512180-use-skills-in-claude>

## Claude Code

```
/plugin marketplace add AIBIO-UK/airbds-metric
/plugin install airbds-assessment@airbds-metric
```
