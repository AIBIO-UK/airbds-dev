# ISSUES

- The spreadsheet uses XLOOKUP and Claude Web complains that this isn't supported by the recalc engine, before replacing the formulas with compatible equivalents
- The symlink for the spreadsheet in `templates` has to be renamed so that the name only contains [a-z][A-Z][0-9]- otherwise Claude Web won't load it.
