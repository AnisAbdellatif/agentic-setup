# agentic-setup

A portable [Claude Code](https://claude.com/claude-code) environment, rebuilt on any macOS or Linux machine by an LLM following [`INSTRUCTIONS.md`](INSTRUCTIONS.md).

## What's in it
- `CLAUDE.md`, `agents/`, `commands/`, `hooks/`: symlinked into `~/.claude` by `scripts/install.sh`.
- `settings.common.json` plus a machine-local private settings file (credentials, never in git): compiled into `~/.claude/settings.json` by `scripts/settings.py`.
- `hooks/guard.py` (blocks force push, `--no-verify`, destructive `rm`, secret reads) and `hooks/format.py` (auto-format on edit).
- `t3/`: config for the T3 Code desktop app.
- `.githooks/pre-commit`: gitleaks scan.
- `CLAUDE.proton-ssh.md`: optional machine-local rules for a Proton Pass SSH agent.

## Deploy
```
claude "Set up this machine by following https://raw.githubusercontent.com/AnisAbdellatif/agentic-setup/main/INSTRUCTIONS.md"   # add "dry run" to preview
```
The agent clones this repo to `~/dev/agentic-setup` itself and asks which components to install. Auth: export `ANTHROPIC_AUTH_TOKEN` in your shell profile, or log in via `claude`.

Verify a machine: `sh scripts/doctor.sh`.

## Make it yours
This is a personal setup. Fork it, replace the `AnisAbdellatif` URLs in `INSTRUCTIONS.md`, and edit `CLAUDE.md` and `settings.common.json` to taste. Read `INSTRUCTIONS.md` before letting an agent run it: it installs plugins and tools and runs shell commands on your machine.

## Update
Edit files here (or via the symlinks), then commit. See "Maintaining this file" in `INSTRUCTIONS.md`.

## License
[MIT](LICENSE). Third-party plugins and skills it installs keep their own licenses (e.g. `academic-research-skills` is CC-BY-NC-4.0).
