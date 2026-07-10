CLAUDE.md was a symlink to AGENTS.md at the repo root (`CLAUDE.md -> AGENTS.md`),
so its content was identical. It was removed as redundant during the repo
cleanup — AGENTS.md at the repo root is now the sole canonical instructions
file. Recreate the symlink (`ln -s AGENTS.md CLAUDE.md` from the repo root) if
a tool that specifically looks for CLAUDE.md (rather than AGENTS.md) needs it
back.
