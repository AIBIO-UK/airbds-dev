CLAUDE.md was a symlink to AGENTS.md at the repo root (`CLAUDE.md -> AGENTS.md`),
so its content was identical. It was removed as redundant during the repo
cleanup.

`AGENTS.md` itself has since also been archived — see [`AGENTS.md`](AGENTS.md)
in this same directory. There is currently no live agent-instructions file at
the repo root. To reactivate: move `AGENTS.md` back to the repo root, and
recreate the symlink (`ln -s AGENTS.md CLAUDE.md` from the repo root) if a
tool that specifically looks for CLAUDE.md (rather than AGENTS.md) needs it
back.
