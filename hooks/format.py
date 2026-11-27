#!/usr/bin/env python3
"""PostToolUse (Edit|Write|MultiEdit): format the edited file with the project's own formatter.
Repo-local tools (node_modules/.bin) run only for repos under a trusted root: one path per line in
~/.config/claude-hooks/trusted-roots (default ~/dev), so a cloned-to-inspect repo runs nothing.
Fails open: always exits 0."""
import json, os, re, shutil, subprocess, sys

JS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".css", ".scss", ".html", ".md", ".yaml", ".yml", ".vue", ".svelte"}


def root_of(path):
    d = os.path.dirname(path)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None


def trusted(root):
    try:
        with open(os.path.expanduser("~/.config/claude-hooks/trusted-roots")) as f:
            roots = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        roots = ["~/dev"]
    real = os.path.realpath(root)
    return any(real.startswith(os.path.realpath(os.path.expanduser(r)) + os.sep) for r in roots)


def up(path, root, name):
    """Nearest file called name between path's dir and root."""
    d = os.path.dirname(path)
    while d.startswith(root):
        if os.path.isfile(os.path.join(d, name)):
            return os.path.join(d, name)
        d = os.path.dirname(d)
    return None


def command(path, root):
    ext = os.path.splitext(path)[1]
    if ext in JS and trusted(root):
        bin_ = os.path.join(root, "node_modules", ".bin")
        if os.access(os.path.join(bin_, "biome"), os.X_OK):
            return [os.path.join(bin_, "biome"), "format", "--write", path]
        if os.access(os.path.join(bin_, "prettier"), os.X_OK):
            return [os.path.join(bin_, "prettier"), "--write", "--ignore-unknown", path]
    if ext in (".py", ".pyi") and shutil.which("ruff"):
        cfg = [up(path, root, n) for n in ("ruff.toml", ".ruff.toml", "pyproject.toml")]
        if any(c and (not c.endswith("pyproject.toml") or "[tool.ruff" in open(c).read()) for c in cfg):
            return ["ruff", "format", path]
    if ext == ".go" and shutil.which("gofmt"):
        return ["gofmt", "-w", path]
    if ext == ".rs" and shutil.which("rustfmt"):
        cargo = up(path, root, "Cargo.toml")
        m = cargo and re.search(r'^edition\s*=\s*"(\d+)"', open(cargo).read(), re.M)
        return ["rustfmt", "--edition", m.group(1) if m else "2021", path]
    return None


def main():
    try:
        inp = json.load(sys.stdin).get("tool_input", {})
        path = os.path.abspath(inp.get("file_path", ""))
        root = os.path.isfile(path) and root_of(path)
        cmd = root and command(path, root)
        if cmd:
            subprocess.run(cmd, cwd=root, timeout=20, capture_output=True)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
