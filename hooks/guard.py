#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks force push, --no-verify, rm -r on / or $HOME, and printing secrets/keys.
Text filter only (not a sandbox); permissions.deny covers the Read tool. Exit 2 = block."""
import json, os, re, shlex, sys

HOME_ARGS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*", "${HOME}", "${HOME}/", "${HOME}/*"}
HOME_ARGS |= {os.path.expanduser("~"), os.path.expanduser("~") + "/*"}
SECRET_PATH = re.compile(r"(\.env(\.\w+)?|\.pem|\.key|id_rsa\w*|id_ed25519\w*|\.netrc|\.git-credentials|\.docker/config\.json|settings\.private\.json|\.credentials\.json)(\W|$)|\.(ssh|aws|gnupg|kube)/|\.config/gh/")
SECRET_ENV = re.compile(r"\$\{?(ANTHROPIC_(AUTH|API)_KEY|GITHUB_TOKEN|GH_TOKEN|NPM_TOKEN|\w*(SECRET|PASSWORD)\w*)")
READERS = {"cat", "less", "more", "head", "tail", "bat", "grep", "rg", "sed", "awk", "cp", "base64", "xxd", "strings", "od", "source", "."}


def segments(cmd):
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:  # unbalanced quotes: fall back to plain split
        toks = cmd.split()
    seg = []
    for t in toks:
        if t and set(t) <= set(";&|()"):
            yield seg
            seg = []
        else:
            seg.append(t)
    yield seg


def reason(cmd):
    if SECRET_ENV.search(cmd) and re.search(r"\b(echo|printf|printenv)\b", cmd):
        return "printing secret env vars is blocked."
    for s in segments(cmd):
        while s and re.fullmatch(r"\w+=.*|sudo|env|command|exec", s[0]):  # skip VAR=x prefixes and wrappers
            s = s[1:]
        if not s:
            continue
        if s[0] == "printenv" and not s[1:]:
            return "printenv without args would dump secrets."
        if s[0] in READERS and any(SECRET_PATH.search(a) for a in s[1:]):
            return "reading secret/key files via Bash is blocked."
        if s[0] == "git" and "--no-verify" in s:
            return "--no-verify skips git hooks (secret scan). Fix the hook failure instead."
        if s[0] == "git" and "push" in s and any(
            a in ("--force", "-f") or re.fullmatch(r"-\w*f\w*", a) and not a.startswith("--") or a.startswith("+") for a in s
        ):
            return "force push is blocked. Use --force-with-lease, or ask the user to push."
        if s[0] == "rm" and any(re.fullmatch(r"-\w*[rR]\w*|--recursive", a) for a in s):
            if HOME_ARGS & {a.rstrip("/") or "/" for a in s}:
                return "recursive rm on / or the home directory is blocked."
    return None


def main():
    try:
        inp = json.load(sys.stdin)
    except ValueError:
        return 0
    r = reason(inp.get("tool_input", {}).get("command", ""))
    if r:
        print(f"guard: {r}", file=sys.stderr)
        return 2
    out = unsandbox(inp)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
