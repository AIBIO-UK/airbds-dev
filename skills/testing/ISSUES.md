# ISSUES

- The spreadsheet uses XLOOKUP and Claude Web complains that this isn't supported by the recalc engine, before replacing the formulas with compatible equivalents
- The symlink for the spreadsheet in `templates` has to be renamed so that the name only contains [a-z][A-Z][0-9]- otherwise Claude Web won't load it.
- A google gem cannot be created directly from a Github repository. At the moment I (justincc) am having to manually update and share a gem as linked in the README. This is a major issue since it means that gems cannot be automatically built and used for testing.
