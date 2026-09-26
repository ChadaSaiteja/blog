---
layout: post
title: "Cut Your Coding Agent's Token Bill in Three Places: Graphify, Ponytail, Caveman"
description: "Cut LLM token usage in any codebase: Graphify to stop re-reading, Ponytail to stop over-building, Caveman to shrink prose. Install, usage, real numbers."
date: 2026-09-26
categories:
  - AI
  - DevTools
tags:
  - llm-tokens
  - ai-agents
  - claude-code
  - codex
  - opencode
  - graphify
  - ponytail
  - caveman
  - context-engineering
  - developer-tools
  - cost-optimization
author: "Saiteja Chada"
reading_time: "16 min read"
draft: false
---

Your coding agent burns tokens in three separate places, and almost every "token saver" on the market targets exactly one of them. That is why so many of them disappoint: they optimize the smallest slice of your bill and advertise it as a percentage of the whole.

This post breaks the bill into its three parts, maps one tool to each, gives you the install and daily-usage commands, and — because the numbers matter here — shows you what each tool's author claims versus what an independent lab actually measured.

| What the agent does | Where the tokens go | Tool |
|---|---|---|
| **Reads** the codebase, logs, test output, diffs | Input tokens, re-read on every turn | **Graphify** |
| **Writes** code it did not need to write | Output tokens now, input tokens forever after | **Ponytail** |
| **Says** things around the code | Output tokens | **Caveman** |

The single most important fact in this article: in an agentic coding session, the bill is dominated by **reading**, not by talking. JetBrains found this the hard way, and it is the reason the reading-side tools matter more than the style-side ones.

---

## The Honest Numbers First

Before any install, here is what is claimed versus what was measured by a third party. The independent numbers come from a JetBrains series by Denis Shiryaev that ran public "token saver" skills through the same paired A/B harness (Harbor sandboxes, SkillsBench tasks, auto-graded verifiers, Claude Code on `claude-sonnet-5`).

| Tool | Advertised | Independently measured | Quality |
|---|---|---|---|
| **Caveman** (skill) | −65% output tokens | **−8.5%** output tokens, ~10% cost (86 paired tasks) | No detectable change (sign test p = 0.82) |
| **RTK** (shell-output compressor) | −60% to −90% | **+7.6% median cost per task** (p = 0.004) | Tie |
| **Ponytail** | −54% code, −22% tokens, −20% cost, −27% time | **−15.4% code** (p = 0.088), **−10.3% cost** (p = 0.004), −11% time (80 paired tasks, 251 trials, ~$246) | No detectable change (65 identical, 9 worse, 6 better) |
| **Graphify** | 71.5× fewer tokens per query | **7.3×** on a pure-code repo (~154k corpus tokens → ~21k per query, range 6.5–8.1×) | Higher key-fact coverage: 70.8% → 82.0% on a ~1M-LOC repo |

Read that table twice. Two lessons:

1. **Ponytail is the only tool in the series that produced a statistically solid cost *saving*.** RTK's result was just as significant, pointing the wrong way.
2. **Graphify's 71.5× headline is real but measured on a mixed corpus** (52 files including research PDFs and images, which inflate the naive "read everything" baseline enormously). On a pure-code repository, expect 5–10×, not 70×.

> [!NOTE]
> Every skill adds input tokens on *every* call, because the agent re-reads its instructions each turn. The Caveman skill's own README puts the full ruleset at roughly 1,000 tokens per call. On terse one-liner Q&A that tax can exceed the savings. The Adobe Research paper [CAVEWOMAN (arXiv:2606.24083)](https://arxiv.org/abs/2606.24083) measured this precisely: compressing **output** cut realized cost 1.4–2.4× per model (up to 3×), while compressing **input** *raised* net cost by ~1.15× on the five-benchmark mean, because models compensate with longer responses even as accuracy collapses.

### Where the money actually is

Ponytail's own benchmark included a "terse prose" control arm using Caveman. The result is the most useful data point in this whole space:

| vs no-skill baseline | LOC | tokens | cost | time | safe |
|---|--:|--:|--:|--:|--:|
| **ponytail** | **−54%** | **−22%** | **−20%** | **−27%** | 100% |
| caveman (terse-prose control) | −20% | **+7%** | +3% | +2% | 100% |
| "YAGNI + one-liners" prompt | −33% | −14% | −21% | −30% | 95% |

Caveman's style rules made the agent write *more* tokens in that arm, because the instruction overhead was larger than the prose it removed. And the bare "write one-liners" prompt cut cost just as much as Ponytail while dropping a safety guard — which is exactly the failure mode Ponytail's ladder is designed to avoid.

Note also where Ponytail's own savings came from: fresh input tokens fell only 3.9% and re-reads 8.4%, **neither statistically significant**. Ponytail attacks the write side, and on that benchmark the write side is where the money moved.

---

## Tool 1 — Graphify: Stop the Agent Re-Reading Your Whole Codebase

### The problem: reading the codebase

Ask an agent "how does authentication work in this repo?" with no map, and it does the only thing it can: open files until it finds the answer. Then it does it again in the next session, and the next. Every one of those opens is input tokens, and most of them are cache-misses you pay full price for.

### What Graphify does

Graphify pre-processes your repository into a **queryable knowledge graph** and writes three artifacts:

```text
graphify-out/
├── graph.html        # interactive — click nodes, search, filter by community
├── GRAPH_REPORT.md   # god nodes, communities, surprising connections, suggested questions
├── graph.json        # the graph itself — query it weeks later
└── cache/            # SHA256 cache — only changed files get re-processed
```

The extraction pipeline is deliberately split:

- **Code** is parsed with tree-sitter across 36 languages — real ASTs, call graphs, docstrings, rationale comments. Deterministic, **no model call, zero LLM credits**.
- **Non-code** (docs, PDFs, SQL, Terraform, images) is read by your agent's own model and tagged as inferred.
- Everything merges into a NetworkX graph, clustered with **Leiden community detection** (graph topology, no embeddings).

Every edge is labelled, and this is the part that makes it trustworthy:

| Tag | Meaning |
|---|---|
| `EXTRACTED` | Came from the AST. This is ground truth. |
| `INFERRED` | A model connected these two. A hypothesis. |
| `AMBIGUOUS` | Could not be fully resolved. |

### Installing Graphify

Requires Python 3.10+.

**Step 1 — install the CLI.** `uv` puts it on PATH automatically and is the recommended path. Alternatives if you do not use `uv`: `pipx install graphifyy`, or `pip install graphifyy`.

```bash
uv tool install graphifyy
```

**Step 2 — register the `/graphify` skill with your agent.**

```bash
graphify install
```

> [!WARNING]
> **The PyPI package name is `graphifyy` with a double `y`** (while the CLI command stays `graphify`). The name is being reclaimed, and there are several unaffiliated `graphify*` packages and repositories on PyPI and GitHub. Install from the project documented at `https://graphify.com/docs` and verify the repository before you trust it with your source tree. Do not `pip install graphify`.

To install the skill into the current repository instead of your user profile:

```bash
graphify install --project
```

That writes `.claude/skills/graphify/SKILL.md` (or `.agents/skills/graphify/SKILL.md` for cross-framework agents) and prints a `git add` hint.

Other platforms, if `graphify install` does not cover yours:

```bash
graphify install --platform gemini
graphify install --platform hermes
graphify install --platform pi
graphify cursor install
graphify kiro install
graphify codex install
graphify amp install
```

Platforms without tool hooks (Aider, Trae, Hermes, OpenClaw, Amp) get the always-on guidance written into `AGENTS.md` instead.

### Build the graph

Inside your agent:

```text
/graphify .
```

Other build modes:

| Command | What it does |
|---|---|
| `/graphify .` | Full build |
| `/graphify . --update` | Incremental, only changed files |
| `/graphify . --watch` | Background watcher — code saves trigger an instant AST-only rebuild, no LLM |
| `/graphify . --mode deep` | Deeper multi-pass analysis |
| `/graphify . --wiki` | Agent-crawlable wiki: `index.md` plus one article per community |
| `graphify hook install` | Post-commit git hook — rebuilds after every commit |

### Query it

Prefer the CLI when you want the answer without spending agent tokens:

```bash
graphify query "what connects auth to the database?"
graphify path "UserService" "DatabasePool"
graphify explain "RateLimiter"
graphify export callflow-html          # Mermaid call-flow diagrams
```

Real output from `graphify explain`:

```text
Node: APIRouter
Source:    routing.py L2210
Community: 2
Degree:    47
```

For an MCP host:

```bash
python -m graphify.serve graphify-out/graph.json
python -m graphify.serve graphify-out/graph.json --transport http --port 8080
```

That exposes 10 graph tools: `query_graph`, `get_node`, `get_neighbors`, `shortest_path`, `get_community`, `god_nodes`, `graph_stats`, `list_prs`, `get_pr_impact`, `triage_prs`.

### The cost, stated honestly

| Operation | Approximate token cost |
|---|---|
| Initial build, 140-file repo (~7 subagents) | ~200k–280k |
| Incremental update, 3 changed files | ~40k |

The initial build is a real one-time investment. It is not free, and Graphify's own cost tracker does not capture subagent usage, so the tool may report zero while your provider invoice says otherwise. Check your provider dashboard, not the tool's number.

Graphify's own benchmark suite adds a useful third data point on a ~1M-LOC production repo (ERPNext): giving a fixed coding agent one Graphify tool lifted key-fact coverage from **70.8%** (grep + read baseline) to **82.0%**, at roughly 140k tokens per query — while "stuffing the whole repo into every turn" cost about 20× the tokens for *lower* coverage.

> [!TIP]
> A `.graphifyignore` file lets you exclude `node_modules`, `dist`, `vendor`, build output, and lockfiles. Do this on the first run. It is the difference between a 30-second build and a 10-minute one, and it keeps junk out of your graph.

### When to skip it

- **Focused implementation sessions.** Clear spec, known files, task-by-task execution. You will not use the graph, and it will not save you anything.
- **Small repositories.** Under roughly 200 files the overhead competes with the benefit — the graph value is structural clarity, not compression.
- **Windows incremental updates.** `--update` has documented problems there: Python's default `cp1252` encoding crashes on Unicode in reports, and the skill's shell quoting was written for Unix. Full rebuilds work fine.

The pattern that held up in long-term field use:

```text
skip --update for small sessions (< 10 files changed)

full rebuild every 3-5 sessions:
/graphify . --wiki

always rebuild after a major architectural change:
/graphify .
```

---

## Tool 2 — Ponytail: Stop the Agent Writing Code It Did Not Need to Write

### The problem: writing unnecessary code

Ask for a date picker and a default agent installs a library, writes a wrapper component, adds a stylesheet, and opens a discussion about timezones. Every one of those lines is output tokens now, and input tokens on every subsequent turn that touches the file — forever. Over-building is the most expensive habit an agent has, and it is invisible in a token report.

### The decision ladder

Ponytail is not a prompt. It is a persistent seven-rung ladder the model climbs before it writes anything:

```text
1. Does this need to exist?    → no: skip it (YAGNI)
2. Already in this codebase?   → reuse it, don't rewrite
3. Stdlib does it?             → use it
4. Native platform feature?    → use it
5. Installed dependency?       → use it
6. Can it be one line?         → one line
7. Only then: the minimum that works
```

Rung 2 is the anti-duplication rung, and it is the one that matters most in an existing codebase. Rung 4 is the one that produces the biggest wins — a date picker collapses from 404 lines to 23 because the browser already has `<input type="date">`.

Two design decisions worth knowing:

- The ladder runs **after** the agent understands the problem, not instead of it. It reads the code the change touches and traces the real flow first. Lazy about the solution, never about reading.
- Validation, error handling, security, and accessibility are explicitly **off the chopping block**. That is the line between Ponytail and a bare "write one-liners" prompt, which cut cost similarly in the benchmark above while dropping a guard.

### Installing Ponytail (Claude Code)

Send these as **two separate prompts** — the install does not work if you paste them together:

```text
/plugin marketplace add DietrichGebert/ponytail
```

```text
/plugin install ponytail@ponytail
```

Node.js must be on your PATH; the plugin runs two small lifecycle hooks. If `node` is missing the skills still work — the always-on activation just stays quiet.

Uninstall:

```text
/plugin remove ponytail
node scripts/uninstall.js    # run BEFORE removing the plugin, to clear its leftover state
```

### Installing Ponytail (Codex, OpenCode, Gemini, and the rest)

**Codex:**

```bash
codex plugin marketplace add DietrichGebert/ponytail
codex plugin add ponytail@ponytail
```

**OpenCode** — add to `opencode.json`:

```json
{ "plugin": ["@dietrichgebert/ponytail"] }
```

**Gemini CLI:**

```bash
gemini extensions install https://github.com/DietrichGebert/ponytail
```

Cursor, Windsurf, Cline, Aider, Copilot Chat, Kiro, Zed, Amp, Jules, Qoder and others read a plain `AGENTS.md` from the repo root with zero setup. The repository ships one, so running Ponytail from a checkout in those tools just works.

### Ponytail Commands

| Command | What it does |
|---|---|
| `/ponytail` | Report the current level |
| `/ponytail lite` | Build what you asked; name the lazier alternative in one line |
| `/ponytail full` | The ladder, enforced. **Default.** |
| `/ponytail ultra` | YAGNI extremist — ships the one-liner and challenges the rest of the requirement |
| `/ponytail off` | Turn it off |
| `/ponytail-review` | Review the current diff for over-engineering; returns a delete-list |
| `/ponytail-audit` | Audit the whole repo, not just the diff |
| `/ponytail-debt` | Harvest the `ponytail:` shortcuts you deferred into a ledger, with upgrade triggers |
| `/ponytail-gain` | The benchmark scoreboard |
| `/ponytail-help` | One-screen command reference |

Set the level for every new session:

```json
// ~/.config/ponytail/config.json   (Windows: %APPDATA%\ponytail\config.json)
{ "defaultMode": "full" }
```

Or with the `PONYTAIL_DEFAULT_MODE` env var (`lite` / `full` / `ultra` / `off`). To keep the ruleset out of read-only search subagents:

```bash
PONYTAIL_SUBAGENT_MATCHER="^general$"    # unanchored regex, case-insensitive, tested against agent_type
```

> [!WARNING]
> **Install as a plugin, not as a bare `SKILL.md`.** JetBrains installed Ponytail as a plain skill file and let the model decide when to use it. Across ten sessions it self-activated **zero** times. Not rarely — never. The `SessionStart` hook is what injects the ruleset whether you ask or not. If you copy the skill file into a skills folder and install nothing else, you will measure exactly zero and conclude the tool does not work.
>
> Every number in every benchmark for this tool comes from the arm where the ruleset was actually injected. The JetBrains team also audited all 251 of their trials afterwards to confirm the ruleset reached the model: 100% in the treatment arm, 0% in the baselines.

### What a real saving looks like

Both of these agents were asked to export a three.js scene to a Blender-ready OBJ file. Both produced a file the verifier accepted. Both wrote the same fiddly loop, because three.js's `OBJExporter` cannot handle instanced meshes. The difference was everything around it.

```javascript
// no skill — 10 statements
const exportRoot = new THREE.Group();
exportRoot.name = 'blender_export_root';
exportRoot.rotation.x = -Math.PI / 2;
exportRoot.add(root);
exportRoot.updateMatrixWorld(true);

const exporter = new OBJExporter();
const objString = exporter.parse(exportRoot);

const outputPath = '/root/output/object.obj';
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, objString);
```

```javascript
// ponytail — the same job, 5 statements
root.rotation.x = -Math.PI / 2;
root.updateMatrixWorld(true);

const obj = new OBJExporter().parse(root);
fs.mkdirSync('/root/output', { recursive: true });
fs.writeFileSync('/root/output/object.obj', obj);
```

Ten statements became five. Same geometry exported, same verifier score of 1.0. The agent rotated the object it already had instead of building a parent to rotate it for itself, and dropped an import on the way.

> [!NOTE]
> The cut concentrates where there is room to over-build. In the JetBrains run, code fell **31%** on large builds and moved by roughly **zero** on tasks that were already lean. The more your agent over-builds, the more this pays. The more disciplined your prompts already are, the less.

---

## Tool 3 — Caveman: Shrink What the Agent Says

### The problem, and the honest size of it

A default agent writes like a cover letter. Caveman makes it write like a field note. Same answer, no throat-clearing:

| Level | "Why does my React component re-render?" |
|---|---|
| Normal | The reason your component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using `useMemo`. **69 tokens** |
| `full` | New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`. **19 tokens** |
| `ultra` | Inline obj prop, new ref, re-render. `useMemo`. |

Code, commands, file paths, and exact error strings are never touched. Security warnings and "are you sure?" confirmations come back in full sentences on their own, then the style resumes.

### The uncomfortable part

That 69 → 19 is a 72% cut, and it is real. It is also **not** what happens in a coding session, because in a coding session most tokens are code and tool calls that the style never touches. JetBrains measured **−8.5% output tokens** on 86 real paired tasks, with quality flat. The 65% headline belongs to chat-style Q&A.

There is a second, less discussed finding from the same research. The Adobe CAVEWOMAN paper measured both channels separately and found they point in opposite directions:

- Compressing the **model's output** cut realized cost 1.4–2.4× per model, up to 3× in the best case.
- Compressing the **human's input** raised net cost — ~1.15× on the five-benchmark mean, up to 1.8× worst-case and 2.7× under stronger compression — because models compensate with longer responses even as accuracy collapses.

So: never let a tool rewrite *your* prompts into caveman-speak.

## Installing Caveman

**Small rock — the skill.** Works in 30+ agents, no account, no API key.

```bash
npx skills add JuliusBrussee/caveman -g
```

**Full installer** — wires Claude Code hooks plus the statusline badge, detects every supported agent, safe to re-run, needs Node.js 22.13+.

```bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

**Windows, PowerShell 5.1+:**

```powershell
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex
```

**Or install just for Claude Code:**

```bash
claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman
```

### Caveman Commands

| Command | What it does |
|---|---|
| `/caveman` | Activate at `full` (the default) |
| `/caveman lite` | Tight but polite — full sentences, no filler or hedging |
| `/caveman ultra` | Stripped to fragments |
| `/caveman wenyan` | Classical Chinese, because someone asked |
| `/caveman off` or `normal mode` | Turn it off |
| `/caveman-commit` | One-line Conventional Commits |
| `/caveman-review` | One finding per line: `L42: null deref. Guard it.` |
| `/caveman-compress CLAUDE.md` | Shrinks a memory file ~46%, keeping every heading, path, and command, with a backup |
| `/caveman-stats` | Recorded session token usage |

Set a default level with `CAVEMAN_DEFAULT_MODE` or `~/.config/caveman/config.json`:

```json
{ "defaultMode": "lite" }
```

Use `"off"` to disable auto-activation entirely.

### The bigger rock: the proxy

This is the part that actually moves the bill, and it is the part most people skip. The skill shrinks what the agent **says**. The proxy shrinks what the agent **reads** — logs, test output, JSON, diffs, search results — by running on your machine between the agent and the provider.

```text
 Your agent  (Claude Code · Codex · Gemini · opencode · Pi · …)
      │   tool output · logs · JSON · diffs · search results
      ▼
 ┌────────────────────────────────────────────┐
 │  caveman proxy   (your machine, your keys)  │
 │  detect() → json · log · code · diff · …    │
 │  originals → local SQLite + recovery handle │
 └────────────────────────────────────────────┘
      │   smaller prompt, same answer
      ▼
 Your provider  (Anthropic · OpenAI · Google · Bedrock · …)
```

```bash
npm install -g @caveman-ai/cli && caveman setup --install

caveman learn          # read your agent history on disk, rank token sinks worst-first
caveman learn implement # hand each fix to your agent, one diff at a time, applied on your yes
caveman claude         # or codex · gemini · aider · kilo · qwen · opencode · hermes
```

```bash
caveman shrink -- pnpm test    # compress noisy command output, byte-exact recoverable
caveman browse <url>           # compressed page instead of a 15,000-token a11y dump
caveman trial -- claude        # A/B a real session, then: caveman trial report
caveman stats
```

Measured by the project on a pinned 54-run Claude Code suite, provider-reported input tokens, every answer checked against an exact oracle:

| Case | Direct Claude Code | Through caveman | Change |
|---|--:|--:|--:|
| CSV outlier hunt | 165,823 | 74,484 | −55.1% |
| Log needle in haystack | 148,807 | 74,068 | −50.2% |
| YAML config drift | 132,124 | 71,027 | −46.2% |
| Test output failure | 150,377 | 108,514 | −27.8% |
| Deployment JSON drift | 147,975 | 108,939 | −26.4% |
| Dashboard HTML alert | 140,687 | 154,641 | **+9.9%** |
| **Total** | **885,793** | **591,673** | **−33.2%** |

18 of 18 answer checks passed. The HTML row is red and it stays red: that case had no compression transform, so the proxy paid its own overhead and won nothing back.

> [!WARNING]
> The caveman CLI sends anonymous usage stats by default — which commands ran and token counts through and cut. It never sends prompts, code, or file paths. Turn it off with `caveman telemetry off` or `DO_NOT_TRACK=1`. The skill and hooks never phone home at all. Note also the split license: the skill and CLI are MIT, but the engine-linked runtime is BSL-1.1 source-available, converting to Apache-2.0 on the earlier of 2030-06-21 or four years after release. If you need OSI-approved code in a commercial product, read `LICENSE` before you deploy the proxy in production.

### When to skip Caveman

- You are billed **per request** rather than per token (GitHub Copilot premium requests, for example) — a shorter answer is the same request.
- Your workload is **pure code generation** with almost no prose to cut.
- You are on terse one-liner Q&A, where the ~1,000-token-per-call ruleset tax can exceed the savings.

There is a real research reason terseness is worth doing anyway. A March 2026 paper, [Brevity Constraints Reverse Performance Hierarchies in Language Models (arXiv:2604.00025)](https://arxiv.org/abs/2604.00025), evaluated 31 models from 0.5B to 405B parameters and found that constraining large models to brief responses improved accuracy by **26.3 percentage points** while cutting outputs ~60% in length. Over-elaboration, not missing knowledge, was the failure mode. A terser agent is a more accurate agent, independent of what it costs.

---

## Putting All Three Together

They do not overlap. The Caveman README puts it well: *Caveman shrinks what the agent says; Ponytail shrinks what it builds. Terse talk about minimal code.*

```text
                    ┌─────────────────────────────────────────┐
  session start ──► │  GRAPHIFY  graph.json + GRAPH_REPORT.md │  orientation
                    │  "how does auth work? blast radius?"     │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
  ticket arrives ──► │  PONYTAIL  7-rung ladder               │  scope
                    │  "does this exist? already here? stdlib?"│
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
  every reply ────► │  CAVEMAN  drop the prose                │  output
                    │  code, errors, paths stay byte-exact     │
                    └─────────────────────────────────────────┘
```

### A realistic session

```text
STEP 1 — orient once per repo, or every 3-5 sessions
/graphify . --wiki
  read GRAPH_REPORT.md, note the god nodes
  add graphify-out/ to .gitignore, or commit it deliberately

STEP 2 — start the session
/ponytail full
/caveman full

STEP 3 — an unfamiliar ticket: let the graph do the traversal
  "how does invoice recalculation connect to the billing scheduler?"
  the agent queries the graph instead of grepping 200 files

STEP 4 — a known ticket: the ladder keeps the diff small
  "add a date range filter to the reports page"
  ponytail checks for an existing helper, then a native <input>,
  then writes 20 lines instead of installing a picker library

STEP 5 — before you commit
/ponytail-review     delete-list for the diff
/caveman-commit      one-line Conventional Commit

STEP 6 — every few sessions
/ponytail-audit      repo-wide over-engineering scan
```

### The order to install in

1. **Ponytail first.** It is two prompts, needs nothing but Node, has the only statistically significant cost saving, and cannot break your build.
2. **Caveman's skill second.** One `npx` command. Free, reversible with `normal mode`, and measurably harmless to quality.
3. **Graphify third.** It is the only one with a real build cost (~200k+ tokens) and a real prerequisite (Python 3.10+), and it pays off only on repositories large enough to make re-reading expensive.
4. **Caveman's proxy last, if at all.** It is the biggest single win on the reading side and also the biggest new component in your request path. Measure it on your own workload before trusting it in production.

---

## Gotchas Worth Knowing Up Front

| Gotcha | What to do |
|---|---|
| **Bare skill files do not self-activate.** Ponytail self-activated zero times in ten sessions when installed as a plain `SKILL.md`. | Install plugins with lifecycle hooks. The hook *is* the mechanism. |
| **The ruleset tax is real.** Every skill re-reads its instructions each turn (~1,000 tokens for the full Caveman skill). | Measure on your workload. Prefer `lite` over `full` for chat-heavy work. |
| **Never compress the human's side of the conversation.** Input compression raised net cost by ~1.15× in the CAVEWOMAN study. | Output style only. Keep your prompts verbose and precise. |
| **Graphify `--update` is fragile on Windows.** cp1252 encoding and Unix-style shell quoting. | Prefer full rebuilds every 3–5 sessions. Set up `.graphifyignore`. |
| **Verify the `graphifyy` package and repo.** Several unaffiliated `graphify*` packages exist while the name is being reclaimed. | Install from the project documented at `https://graphify.com/docs`. |
| **Small samples lie.** A 10-task smoke run said Ponytail made things 9.6% *more* expensive with quality collapsing 0.51 → 0.31. The full 80-task run said −10.3% cheaper. | Never trust k=1. Run enough paired tasks to see the spread. |
| **"No quality difference detected" is not "quality unchanged."** | That was a significance test, not a non-equivalence test. Both this post and the source studies say so explicitly. |
| **Your own re-reading dominates.** Fresh input tokens fell only 3.9% under Ponytail (p=0.085, not significant). | If your bill is mostly input, optimize the reading side, not the writing side. |

---

## Measure It Yourself

Every number in this post came from someone else's benchmark. Yours will differ, because your model, your task mix, and your caching behaviour are yours. The tools agree on this point: *that A/B outranks every number on the readme.*

**Cheapest measurement (no install):** run the same ticket twice on the same model — once normally, once with the tools active — and diff `git diff --stat` plus your provider's token report.

```bash
git diff --stat
git diff --numstat | awk '{ add += $1 } END { print add " lines added" }'
```

**Freeze the variable that matters.** Pin the model, keep the task identical, and reset the session between runs. A ten-task smoke run is where people get burned — JetBrains published exactly that failure: a smoke run that would have produced "Ponytail makes agents worse" if they had stopped there.

**Read the distribution, not the mean.** One long-context session can bill 25× normal and destroy an average. Per-task medians plus a paired test are the minimum.

**Caveman ships its own harness**, if you want a fully automatic A/B:

```bash
caveman disable claude     # if you already wrapped claude
caveman trial -- claude
caveman trial report
caveman enable claude
```

**Or just read the bill.** Run the same task with and without, then compare the provider's usage page. That number is the only one that cannot be argued with.

---

## The Copy-Paste Checklist

```bash
node --version          # v22.13+ for the full Caveman installer
python --version        # 3.10+ for Graphify
```

**Step 1 — Ponytail: stop over-building (biggest solid win)**

```text
Claude Code — send these as TWO SEPARATE prompts:
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

Then run `/ponytail full` inside your agent.

**Step 2 — Caveman: shrink the prose (free, reversible)**

```bash
npx skills add JuliusBrussee/caveman -g
```

Then run `/caveman full` inside your agent. Exit with `normal mode`.

**Step 3 — Graphify: stop re-reading (build once, query forever)**

```bash
uv tool install graphifyy     # note the double-y
graphify install
```

Then run `/graphify .` inside your agent. Add a `.graphifyignore` before the first build.
**Step 4 — Optional: shrink what the agent READS**

```bash
npm install -g @caveman-ai/cli
caveman setup --install
caveman learn                 # find your token sinks first
caveman telemetry off         # if you want zero analytics
```

```text
node_modules/
dist/
build/
vendor/
target/
*.lock
package-lock.json
coverage/
__pycache__/
.venv/
```

---

## Key Takeaways

- **A coding agent's bill has three leaks, and no single tool plugs all of them.** Reading the codebase, writing unnecessary code, and narrating around the code are separate costs with separate fixes.
- **Ponytail is the one to install first.** It is the only tool in the independent benchmark series with a statistically significant cost *saving* (−10.3%, p = 0.004), it needs nothing but Node, and it cannot break your build. Expect ~10% cheaper, not 54% less code, unless your agent genuinely over-builds.
- **Caveman's prose style is cheap, harmless, and small.** −8.5% output tokens measured on real coding tasks, quality flat. Do not expect the 65% headline — that number is for chat, not for code. The *proxy* is the interesting part: −33.2% input tokens on the reading side, with the original recoverable byte-for-byte.
- **Graphify is an orientation tool, not an implementation tool.** Build it once, query it when you are lost, skip it when you already know where you are working. On a pure-code repository expect 5–10×, not 71.5×.
- **Never compress your own prompts.** Two separate studies found output compression cuts cost and input compression raises it, because models compensate with longer responses.
- **Measure it yourself.** Every number above is someone else's benchmark, and small samples lie in both directions. Run the same ticket with and without, then read your provider's invoice.

---

## References

**Graphify**
- [graphify.com/docs](https://graphify.com/docs) — canonical quickstart
- [Graphify field report: 7.3× on a real codebase](https://exchangepedia.com/articles/graphify-honest-benchmark-real-codebase.html)

**Ponytail**
- [github.com/DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) — source, MIT
- [ponytail.dev](https://ponytail.dev/)

**Caveman**
- [github.com/JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — source

**Research**
- [CAVEWOMAN: How Large Language Models Behave Under Linguistic Input and Output Compression (arXiv:2606.24083)](https://arxiv.org/abs/2606.24083) — Adobe Research; output compression 1.4–2.4× cheaper, input compression ~1.15× *more* expensive
- [Brevity Constraints Reverse Performance Hierarchies in Language Models (arXiv:2604.00025)](https://arxiv.org/abs/2604.00025) — brevity constraints, +26.3pp accuracy on large models

