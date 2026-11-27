#!/bin/sh
# Read-only health check of this setup. Prints "ok <what>", "MISSING <what>: <fix>" or "WARN <what>: <fix>".
# Last line: "doctor: <n> missing". Exits 1 when n > 0.
REPO=$(cd "$(dirname "$0")/.." && pwd)
C="$HOME/.claude"
n=0
ok() { echo "ok      $1"; }
miss() { echo "MISSING $1: $2"; n=$((n + 1)); }
warn() { echo "WARN    $1: $2"; }
skipped() { grep -q "\"$1\"" "$C/setup-selection.json" 2>/dev/null; }

for i in CLAUDE.md agents commands hooks; do
  [ "$(readlink "$C/$i")" = "$REPO/$i" ] && ok "link ~/.claude/$i" || miss "link ~/.claude/$i" "sh $REPO/scripts/install.sh --links-only"
done
[ -w "$REPO/CLAUDE.md" ] && miss "CLAUDE.md read-only" "chmod 444 $REPO/CLAUDE.md" || ok "CLAUDE.md read-only"
if [ -d "$HOME/.codex" ]; then
  [ "$(readlink "$HOME/.codex/AGENTS.md")" = "$REPO/CLAUDE.md" ] && ok "link ~/.codex/AGENTS.md" || miss "link ~/.codex/AGENTS.md" "sh $REPO/scripts/install.sh --links-only"
fi

P="$C/settings.private.json"
if [ ! -f "$P" ]; then miss "settings.private.json" "sh $REPO/scripts/install.sh --settings-only"
elif [ "$(ls -l "$P" | cut -c1-10)" != "-rw-------" ]; then miss "settings.private.json mode 600" "chmod 600 $P"
elif grep -q '<your' "$P"; then miss "settings.private.json filled in" "replace the placeholder in $P"
else ok "settings.private.json"; fi
[ -f "$C/settings.json" ] && [ ! -L "$C/settings.json" ] && ok "settings.json compiled" || miss "settings.json compiled" "python3 $REPO/scripts/settings.py build"

[ "$(git -C "$REPO" config core.hooksPath)" = ".githooks" ] && ok "git hooks (secret scan)" || miss "git hooks (secret scan)" "sh $REPO/scripts/install.sh --githooks-only"

for t in claude git jq node npm python3 gitleaks; do
  command -v "$t" >/dev/null && ok "$t" || miss "$t" "install $t (INSTRUCTIONS.md §1)"
done
skipped tokenade || { command -v tokenade >/dev/null && ok tokenade || miss tokenade "npm install -g @tokenade/cli"; }
skipped plugin:goldfish || { command -v bun >/dev/null && ok bun || miss bun "https://bun.sh"; }
command -v uv >/dev/null && ok uv || warn uv "needed by graphify/agent-estimate"

# plugins enabled in the compiled settings but not installed
out=$(python3 - "$C" <<'EOF'
import json, os, sys
def load(p):
    try: return json.load(open(os.path.join(sys.argv[1], p)))
    except Exception: return {}
inst = load("plugins/installed_plugins.json").get("plugins", {})
for k, v in load("settings.json").get("enabledPlugins", {}).items():
    if v: print(f"ok      plugin {k}" if k in inst else f"MISSING plugin {k}: claude plugin install {k} --scope user")
EOF
)
[ -n "$out" ] && echo "$out"
n=$((n + $(printf '%s\n' "$out" | grep -c '^MISSING')))

if [ "$(readlink "$C/CLAUDE.local.md")" = "$REPO/CLAUDE.proton-ssh.md" ]; then
  SSH_AUTH_SOCK="$HOME/.ssh/proton-pass-agent.sock" ssh-add -l >/dev/null 2>&1 && ok "Proton Pass SSH agent" || warn "Proton Pass SSH agent" "pass-cli ssh-agent daemon start (pass-cli login if logged out)"
fi

echo "doctor: $n missing"
[ "$n" -eq 0 ]
