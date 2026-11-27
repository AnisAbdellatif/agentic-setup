#!/usr/bin/env python3
"""Self-check for guard.py: python3 hooks/test_guard.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from guard import reason

blocked = ["git push --force", "git push -f origin main", "git push origin +main", "cd x && git push -fu origin b",
           "git commit --no-verify -m x", "rm -rf /", "rm -rf ~/", "sudo rm -fr $HOME", "rm -r -f /*",
           "rm -rf " + os.path.expanduser("~"), "echo hi; rm -Rf ~", "cat ~/.ssh/id_ed25519", "cat .env", "grep x app/.env.local", "head server.pem",
           "echo $GITHUB_TOKEN", "printenv", "cat a | base64 ~/.aws/credentials"]
allowed = ["git push --force-with-lease", "git push -u origin main", "git commit -m 'git push --force'",
           "rm -rf ./build", "rm -rf ~/tmp/x", "rm -f /tmp/a", "echo --no-verify", "ls -la /", "cat README.md", "ssh-add -l", "cat .envrc.md", "echo hi"]
bad = [c for c in blocked if not reason(c)] + [c for c in allowed if reason(c)]
assert not bad, bad
print("guard ok")
