# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

## Keep the environment reproducible
Whenever you install or add a new plugin, marketplace, skill, agent, command, MCP server, hook, or required env var for Claude Code or T3 Code, also record it in `INSTRUCTIONS.md` in the agentic-setup repo (the directory `~/.claude/CLAUDE.md` is symlinked into; find it with `dirname "$(readlink ~/.claude/CLAUDE.md)"`). Record a CLI tool or app only when Claude needs it to work: a skill, plugin, MCP server or hook depends on it (e.g. REA and its analysis engines, tokenade, graphify, typst/d2 for their skills). General dev tools and apps (Docker/OrbStack, Kamal, editors, language runtimes for projects) don't belong there; they go in the separate dev-environment setup repo. `~/.claude/settings.json` is compiled from the repo's `settings.common.json` + `~/.claude/settings.private.json` (secrets, base URL): after changing settings (plugins/marketplaces go in `enabledPlugins`, `extraKnownMarketplaces`), run `python3 <repo>/scripts/settings.py` to fold the change into the right source file and rebuild, then commit `settings.common.json`. Never put secrets in the repo.

## Default git branch
Use `main`, not `master`, as the default branch. When creating a new repo, `git init -b main` (or `git branch -m main` before the first commit) and push as `main`.

<!-- tokenade-scaffold -->
## Explore code with the `tokenade` CLI (cheaper than reading whole files)
Use these only when you don't yet know where code lives — if you know the path, open it directly:
`tokenade map` (repo structure; `map <path>` for one subtree) · `skeleton <file…>` (signatures) · `query <symbol…>` (locate a symbol) · `impact <file…>` (dependents) · `semantic "<query>"` (search by meaning). They take MANY targets per call (`tokenade skeleton a.rs b.rs c.rs`) — batch in ONE turn.

## Reading documents & media
tokenade can read .pdf .docx .doc .xlsx .xls .xlsb .pptx .ppt .odt .ods .odp .odg .epub .rtf .fb2 .msg (and their flat-XML, macro-enabled and template variants) (extracted text), .mp4 .mkv .mov .webm .avi .mp3 .wav .m4a .flac .ogg .opus (and other common containers) (what the file is, plus a transcript when available) and .png .jpg .jpeg .gif .webp .bmp .tif .tiff .ico .tga .pnm .pbm .pgm .ppm .qoi .hdr (the text they show, when a local tesseract is installed) — your own file reader cannot. Use:
`tokenade read <file>` — the document as text
`tokenade read <file> --prompt "q1, q2"` — only the passages answering your questions; several questions in ONE comma-separated call is the CHEAPEST option in tokens spent, answering each under its own heading in ONE round-trip instead of re-sending the context once per question.

## Searching the web
`tokenade search "<query>"` — one query, fanned out across several independent search engines, merged, deduped and ranked by cross-engine agreement. Returns title/url/snippet only, so it costs a fraction of reading a results page. Add `--json` for machine-readable output.
Follow a result with `tokenade web <url>` to read the page itself.

## Fetching or searching several things
Do them in ONE call — `tokenade web <url1> <url2> …` / `tokenade search "<q1>" "<q2>" …` — they run concurrently, so you pay ONE round-trip instead of N and never re-send the context each extra turn would have re-sent.

## Compute over data with `tokenade exec`
`tokenade exec --lang python --script '<code>'` (also bash/sh/node/ruby/awk/jq/perl) runs a capped subprocess with a scrubbed env — your permissions, not a jail — and returns ONLY its stdout. Data you PIPE in reaches the script's stdin (`cmd | tokenade exec …`), so a big output is filtered where it is produced instead of entering your context. Use it to COMPUTE over data — filter/aggregate a large or structured output, pull facts across SEVERAL files, or apply one mechanical edit across many files (migration, find-replace) — in ONE script, not one command per item. It is NOT a file reader: to read content, use the parallel reads above, not `exec`. Keep scripts SHORT (aim ≤ ~20 lines): exec is for throwaway one-shot computation, not for code you will edit and iterate on — every script char is billed as output, and a long script usually means a simpler command (or a real file you Write once and run) does it cheaper. Long or quote-heavy script? `--script-file <path>` (or `--script -` on stdin) avoids shell quoting entirely.

## Commands
If you do not have tokenade hooks, use `tokenade wrap '<cmd>'` to wrap all your commands — `tokenade health` says whether they are INSTALLED, and names the fix when they are not, so you never have to guess. If there is an opportunity for compacting noisy output, tokenade will find it — and you will waste fewer tokens.
An absolute path (`/usr/bin/git`) is intercepted exactly like `git` when hooks are installed; where interception goes through your PATH instead, only the bare name is seen — so prefer the bare name if you are not sure which you have.
`wrap` keeps the exit code exactly, and MERGES stderr into stdout — the two streams are compacted as one. `tokenade wrap '''cmd''' 2>err.log` therefore writes an empty err.log; redirect from the wrapped command instead (`tokenade wrap '''cmd 2>err.log'''`).

## Keep output lean
Keep prose terse and code minimal — every token you write is billed as output.
- **Prose:** answer directly — no preamble, recap, tool-call narration, summary, or emoji. Drop articles, filler (*just/really/basically/simply*) and hedging; fragments fine; short word over long.
- **Output:** don't paste long raw output — quote the shortest decisive line. No decorative tables.
- **Code:** write the least that works; reuse before adding (`query` / `skeleton` / `impact`, stdlib, platform feature — YAGNI).
- **Verbatim:** keep code, identifiers, API/CLI names and error strings exact — never abbreviate or paraphrase. Keep the user's language.
- **Correctness first:** fix root causes not symptoms, don't downgrade the algorithm, don't guess APIs/flags/versions — verify.
- **Full prose where terseness could mislead:** security/data-loss warnings, irreversible-action confirmations, multi-step sequences.
- Applies to the subagents you spawn.
<!-- /tokenade-scaffold -->

# Anti-loop execution rules

1. Never read the same file more than once unless it has changed.
2. Never execute the same command twice with identical arguments unless the previous execution failed for a clearly identified reason.
3. Keep track of files already inspected and commands already executed.
4. After executing a command, inspect its output before deciding what to do next.
5. Do not repeat a tool call just to reconfirm its result.
6. If a tool call fails, diagnose the error and change your approach.
7. If you cannot make progress after two attempts, stop and explain the blocker.
8. Do not restart analysis from scratch after receiving tool output.
9. Prefer targeted file reads over repeatedly scanning entire files.
10. Once the requested changes are implemented and verified, STOP using tools and provide the final response.
11. If you are an orchestrator, check periodically for your children (subagents) for hanging or looping behavior. If you are a subagent, if you find yourself looping report directly to your orchestrator.

## Subagent model selection
Always invoke the `model-chooser` skill whenever spawning or delegating to subagents, or deciding which model to choose for a task.

## Delegation: orchestrator designs, subagents implement
When delegating code work, do the design yourself first: read the code, then give each subagent
a file-level spec (files to create/modify, types + signatures, integration points, step order,
acceptance checks). Subagents implement, compile, test and commit; they don't design.

## Machine-local instructions
@~/.claude/CLAUDE.local.md
