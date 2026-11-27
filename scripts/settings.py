#!/usr/bin/env python3
"""Compile ~/.claude/settings.json = settings.common.json (this repo) + ~/.claude/settings.private.json.

  sync  (default) pull, then build
  build  write the merge (private wins; dicts merge, other values replace)
  Selection: ~/.claude/setup-selection.json {"skip": ["tokenade", "plugin:ponytail", ...]} filters the build
  (tokenade hooks + statusLine, named plugins and their marketplaces); written by the setup interview.
  pull   fold edits that Claude/tools made to ~/.claude/settings.json back into the source files:
         keys already in the private file stay private, new env vars named like a secret or
         base URL go private, everything else goes to settings.common.json
"""
import copy, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~/.claude")  # not CLAUDE_CONFIG_DIR: that may point at another folder
COMMON = os.path.join(REPO, "settings.common.json")
PRIVATE = os.path.join(HOME, "settings.private.json")
OUT = os.path.join(HOME, "settings.json")
SNAP = os.path.join(HOME, "settings.last-build.json")  # last build, to tell tool edits from source edits
PRIVATE_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|BASE_URL", re.I)
SEL = os.path.join(HOME, "setup-selection.json")
MISSING = object()


def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save(p, d, mode):
    tmp = p + ".tmp"
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode), "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.chmod(tmp, mode)
    os.replace(tmp, p)  # replaces a symlink itself, not its target


def norm(v):
    """Make a value portable before it goes into the shared file: $HOME, bare tokenade."""
    if isinstance(v, str):
        v = re.sub(r"'\\''(?:/opt/homebrew/bin|/usr/local/bin)/tokenade'\\''", "tokenade", v)
        v = re.sub(r"'\\''" + re.escape(os.path.expanduser("~")) + r"/(\.tokenade/debug\.log)'\\''", r'"$HOME/\1"', v)
        return re.sub(r"(?:/opt/homebrew/bin|/usr/local/bin)/tokenade\b", "tokenade", v)
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return [norm(x) for x in v] if isinstance(v, list) else v


def select(d):
    skip = set(load(SEL).get("skip", []))
    if not skip:
        return d
    d = copy.deepcopy(d)
    if "tokenade" in skip:
        d.pop("statusLine", None)
        for ev, groups in list(d.get("hooks", {}).items()):
            for g in groups:
                g["hooks"] = [h for h in g["hooks"] if "tokenade" not in h.get("command", "")]
            d["hooks"][ev] = [g for g in groups if g["hooks"]]
            if not d["hooks"][ev]:
                del d["hooks"][ev]
    for s in skip:
        if s.startswith("plugin:"):
            for k in [k for k in d.get("enabledPlugins", {}) if k.split("@")[0] == s[7:]]:
                d["enabledPlugins"].pop(k)
                d.get("extraKnownMarketplaces", {}).pop(k.split("@")[1], None)
    return d


def merge(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def flat(d, pre=()):
    r = {}
    for k, v in d.items():
        r.update(flat(v, pre + (k,)) if isinstance(v, dict) and v else {pre + (k,): v})
    return r


def has(d, path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return False
        d = d[k]
    return True


def put(d, path, v):
    for k in path[:-1]:
        if not isinstance(d.get(k), dict):
            d[k] = {}
        d = d[k]
    d[path[-1]] = v


def drop(d, path):
    chain = []
    for k in path[:-1]:
        if not isinstance(d.get(k), dict):
            return
        chain.append((d, k))
        d = d[k]
    d.pop(path[-1], None)
    for parent, k in reversed(chain):  # prune dicts the removal emptied
        if parent[k]:
            break
        parent.pop(k)


def pull():
    if not os.path.isfile(OUT) or os.path.islink(OUT):
        return []
    common, private = load(COMMON), load(PRIVATE)
    before = flat(load(SNAP) if os.path.exists(SNAP) else select(merge(common, private)))
    after = flat(load(OUT))
    changed = []
    for path in sorted(set(before) | set(after)):
        new = after.get(path, MISSING)
        if before.get(path, MISSING) == new:
            continue
        if new is MISSING:
            drop(common, path)
            drop(private, path)
        elif has(private, path) or (not has(common, path) and path[0] == "env" and PRIVATE_ENV.search(path[-1])):
            put(private, path, new)
        else:
            put(common, path, norm(new))
        changed.append(".".join(path))
    if changed:
        save(COMMON, common, 0o644)
        save(PRIVATE, private, 0o600)
    return changed


def build():
    out = select(merge(load(COMMON), load(PRIVATE)))
    wrote = os.path.islink(OUT) or load(OUT) != out
    if wrote:  # skip no-op writes (Claude reloads on change)
        save(OUT, out, 0o600)  # holds secrets
    if load(SNAP) != out:
        save(SNAP, out, 0o600)
    return wrote


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd not in ("sync", "build", "pull"):
        sys.exit(__doc__)
    if cmd in ("sync", "pull"):
        changed = pull()
        print("pulled: " + (", ".join(changed) if changed else "nothing"))
    if cmd in ("sync", "build"):
        print(f"{'built' if build() else 'unchanged'}: {OUT}")


if __name__ == "__main__":
    main()
