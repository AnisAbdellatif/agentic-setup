# agentic-setup
Portable Claude Code environment. `~/.claude/{CLAUDE.md,agents,commands,hooks}` are symlinks into this repo and `settings.json` is compiled from it (`scripts/install.sh`); an LLM does the rest by following `INSTRUCTIONS.md`. Check a machine with `sh scripts/doctor.sh`.

## Deploy
```
claude "Set up this machine by following https://raw.githubusercontent.com/AnisAbdellatif/agentic-setup/main/INSTRUCTIONS.md"   # add "dry run" to preview
```
The agent clones this repo to `~/dev/agentic-setup` itself; no manual clone needed.
Auth: export `ANTHROPIC_AUTH_TOKEN` in your shell profile, or log in via `claude`.

## Update
Edit files here (or via the symlinks), then commit. See "Maintaining this file" in `INSTRUCTIONS.md`.
