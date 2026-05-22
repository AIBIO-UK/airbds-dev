# README

This directory contains skills that can be imported into AI assistants to conduct AIRBDS assessments.

Skills being tested are in `testing/`

There are no production skills yet.

We recommend you use the most capable model you have to perform the assessment.

# Installation instructions

There are currently only installation instructions for Claude Web.

Other instructions to follow.

When a skill is installed the assistant will automtically pick it up when relevant. So to perform an assessment you can prompt something like "Please perform an AIRBDS assessment on <dataset-url>", e.g. "Please perform an AIRBDS assessment on https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7"

## Claude Web (claude.ai) and Claude Desktop

### Before you start

You need **Code execution and file creation** turned on: 

- **Free, Pro, Max:** go to [Settings → Capabilities](https://claude.ai/settings/capabilities) and toggle it on. 
- **Team:** enabled by default.
- **Enterprise:** an Owner must enable both **Code execution and file creation** and **Skills** in [Organization settings → Skills](https://claude.ai/admin-settings/skills) first.

### Install the skill

1. [Download the skill](https://github.com/AIBIO-UK/airbds-metric/releases/download/testing/airbds-assessment-skill.zip)
2. Go to [Customize → Skills](https://claude.ai/customize/skills).
3. Click the **+** button, then **Create skill → Upload a skill**.
4. Upload the skill.

The skill appears in your Skills list, enabled by default.

### Reference

Anthropic's full guide: <https://support.claude.com/en/articles/12512180-use-skills-in-claude>

## Gemini

For Gemini, the skill has to be run as a 'Gem'. This either has to be done:

- By going to [this shared Google Gem URL](https://gemini.google.com/gem/14YUoz1uJqOSO0YA0jty4vrux3FoU_dBU?usp=sharing) or
- Manually from this repository, using the contents of the SKILL.md and uploading the template file

You will need to have already registered for Google Gemini for the link to work. We strongly recommend that you use the latest Pro model to run the assessment.
