#!/bin/sh
# Deterministic part of INSTRUCTIONS.md: links, git hooks, settings build. Idempotent.
# Each line starts with a status word: ok (nothing changed), link/add (wrote something),
# skip (left alone, reason given), SKIP (blocked: fix by hand). A second run prints no link/add.
# Usage: install.sh [--links-only | --githooks-only | --settings-only]
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
C="$HOME/.claude"
TS=$(date +%Y%m%d-%H%M%S)

link() { # link <target> <linkpath>
  if [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]; then echo "ok   $2"; return; fi
  if [ -e "$2" ] || [ -L "$2" ]; then mv "$2" "$2.bak.$TS" && echo "add  $2.bak.$TS (backup)"; fi
  ln -sfn "$1" "$2" && echo "link $2 -> $1"
}

links() {
  mkdir -p "$C"
  for i in CLAUDE.md agents commands hooks; do link "$REPO/$i" "$C/$i"; done
  # git drops the mode; read-only stops tokenade's cascade_dedup from stripping the file (INSTRUCTIONS §2)
  if [ -w "$REPO/CLAUDE.md" ]; then chmod 444 "$REPO/CLAUDE.md" && echo "add  chmod 444 CLAUDE.md"; else echo "ok   CLAUDE.md read-only"; fi
  if [ -d "$HOME/.codex" ]; then link "$REPO/CLAUDE.md" "$HOME/.codex/AGENTS.md"; else echo "skip ~/.codex/AGENTS.md (no ~/.codex)"; fi
}

githooks() {
  if [ "$(git -C "$REPO" config core.hooksPath)" = ".githooks" ]; then echo "ok   core.hooksPath"
  else git -C "$REPO" config core.hooksPath .githooks && echo "add  core.hooksPath=.githooks"; fi
  command -v gitleaks >/dev/null || echo "SKIP gitleaks missing: commits will fail until installed (brew install gitleaks)"
}

settings() {
  P="$C/settings.private.json"
  if [ -f "$P" ]; then echo "ok   $P"
  else (umask 077; cp "$REPO/settings.private.example.json" "$P") && echo "add  $P (fill in ANTHROPIC_AUTH_KEY)"; fi
  python3 "$REPO/scripts/settings.py" build | sed -e 's/^built/add  built/' -e 's/^unchanged/ok   unchanged/'
}

case "${1:-}" in
  --links-only) links ;;
  --githooks-only) githooks ;;
  --settings-only) settings ;;
  "") links; githooks; settings ;;
  *) sed -n 2,6p "$0"; exit 2 ;;
esac
