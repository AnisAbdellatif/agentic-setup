## SSH: Proton Pass agent
SSH keys normally live in the Proton Pass SSH agent (`pass-cli ssh-agent`), a daemon on `~/.ssh/proton-pass-agent.sock` (NOT `proton-pass-ssh-agent.sock`, NOT the macOS launchd agent). Host aliases come from `~/.ssh/config.d/protonpass.conf` (generated; never edit).
Before the first SSH/git-over-SSH action in a chat, check once: `SSH_AUTH_SOCK="$HOME/.ssh/proton-pass-agent.sock" ssh-add -l` (exit 0 + key list = agent is up).
1. Agent up: `export SSH_AUTH_SOCK="$HOME/.ssh/proton-pass-agent.sock"` and use it. Plain `ssh <host>` / `git`; no `-i`, no `ssh-add` of files, no new keys, no extra `ssh-agent`.
2. Agent down (socket missing, "No such file", "connection refused", no keys): try `pass-cli ssh-agent daemon start` once, re-check; if still down, just try connecting normally (default `ssh`, whatever keys/config exist).
3. Still fails: stop. Tell the user the connection failed and suggest checking the Proton Pass agent (`pass-cli ssh-agent daemon status`, `pass-cli login` if logged out) as the likely cause. Don't work around it (no key creation, no password prompts, no config edits).
- Use `-o BatchMode=yes` so failures are fast instead of hanging.
- Non-interactive shells read only `~/.zshenv` for `SSH_AUTH_SOCK`; keep it identical to `.zshrc`.
