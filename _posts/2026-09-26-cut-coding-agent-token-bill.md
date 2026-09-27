---
layout: post
title: "Cut Your Coding Agent's Token Bill in Three Places: Graphify, Ponytail, Caveman"
description: "Where an agent's tokens actually go, one tool for each of the three leaks, and what an independent benchmark measured versus what each tool advertises."
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
  - cost-optimization
author: "Saiteja Chada"
reading_time: "8 min read"
draft: false
---

An agent burns tokens in three separate places, and almost every "token saver" targets exactly one of them. That is why so many disappoint: they optimise the smallest slice of the bill and advertise it as a percentage of the whole.

| What the agent does | Where the tokens go | Tool |
|---|---|---|
| **Reads** the codebase, logs, test output, diffs | Input tokens, re-read every turn | **Graphify** |
| **Writes** code it did not need to write | Output now, input forever after | **Ponytail** |
| **Says** things around the code | Output tokens | **Caveman** |

The part that surprises people: the bill is dominated by **reading**, not by talking.

---

## The Numbers First

Before any install, what is advertised versus what an independent lab measured. The independent figures come from a JetBrains series that ran public token-saver skills through one paired A/B harness — Harbor sandboxes, SkillsBench tasks, auto-graded verifiers, Claude Code on `claude-sonnet-5`.

| Tool | Advertised | Independently measured | Quality |
|---|---|---|---|
| **Ponytail** | −54% code, −22% tokens, −20% cost, −27% time | **−15.4% code** (p = 0.088), **−10.3% cost** (p = 0.004), −11% time | No detectable change (80 paired tasks, 251 trials, ~$246) |
| **Caveman** (skill) | −65% output tokens | **−8.5%** output tokens (86 paired tasks) | No detectable change (sign test p = 0.82) |
| **Graphify** | 71.5× fewer tokens per query | **7.3×** on a pure-code repo (~154k corpus tokens → ~21k per query) | Key-fact coverage 70.8% → 82.0% on a ~1M-LOC repo |
| **RTK** (shell-output compressor) | −60% to −90% | **+7.6% median cost per task** (p = 0.004) | Tie |

Two lessons. **Ponytail is the only tool in the series with a statistically solid cost saving** — RTK's result was equally significant, pointing the wrong way. And **Graphify's 71.5× headline was measured on a mixed corpus** (52 files including research PDFs and images, which inflate the naive "read everything" baseline enormously). On a pure-code repository, expect 5–10×.

Ponytail's savings came from the write side specifically: fresh input tokens fell only 3.9% and re-reads 8.4%, neither statistically significant. Its own benchmark included a terse-prose control arm, which made the agent write *more* tokens — the instruction overhead outweighed the prose it removed.

> [!NOTE]
> Every skill adds input tokens on *every* call, because the agent re-reads its instructions each turn. The full Caveman ruleset is roughly 1,000 tokens per call. On terse one-liner Q&A that tax can exceed the savings.

---

## Graphify: Stop Re-Reading the Codebase

Ask an agent "how does authentication work in this repo?" with no map and it does the only thing it can: open files until it finds the answer. Then it does it again next session, and the next. Each open is input tokens, and most are cache-misses you pay full price for.

Graphify pre-processes the repository into a queryable knowledge graph:

```text
graphify-out/
├── graph.html        # interactive — click nodes, search, filter by community
├── GRAPH_REPORT.md   # god nodes, communities, surprising connections
├── graph.json        # the graph itself — query it weeks later
└── cache/            # SHA256 — only changed files get re-processed
```

The extraction pipeline is deliberately split. **Code** is parsed with tree-sitter across 36 languages — real ASTs, call graphs, docstrings, rationale comments. Deterministic, no model call, zero LLM credits. **Non-code** (docs, PDFs, SQL, Terraform) is read by your agent's own model and tagged as inferred. Everything merges into a NetworkX graph clustered with Leiden community detection.

Every edge is labelled, which is what makes it trustworthy:

| Tag | Meaning |
|---|---|
| `EXTRACTED` | Came from the AST. Ground truth. |
| `INFERRED` | A model connected these two. A hypothesis. |
| `AMBIGUOUS` | Could not be fully resolved. |

### Install Graphify

```bash
uv tool install graphifyy     # the PyPI name has a double y
graphify install              # registers the /graphify skill with your agent
```

Then build and query it from inside your agent:

```text
/graphify .                  # full build
/graphify . --update         # incremental, changed files only
/graphify . --wiki           # agent-crawlable wiki, one article per community
```

```bash
graphify query "what connects auth to the database?"
graphify path "UserService" "DatabasePool"
graphify explain "RateLimiter"
```

> [!WARNING]
> The PyPI package is `graphifyy` with a double `y` (the CLI command stays `graphify`). The name is being reclaimed and there are several unaffiliated `graphify*` packages. Install from the project documented at `https://graphify.com/docs` and verify the repository before pointing it at your source tree.

> [!WARNING]
> **`--update` is fragile on Windows.** Python's default `cp1252` encoding crashes on Unicode in reports, and the skill's shell quoting assumes Unix. Full rebuilds work fine. Prefer a full rebuild every 3–5 sessions.

### What it costs

| Operation | Approximate token cost |
|---|---|
| Initial build, 140-file repo (~7 subagents) | ~200k–280k |
| Incremental update, 3 changed files | ~40k |

The build is a real one-time investment. Graphify's own cost tracker does not capture subagent usage, so the tool may report zero while your provider invoice says otherwise — check the provider dashboard, not the tool's number.

### When to skip Graphify

- **Focused implementation sessions.** Clear spec, known files. You will not use the graph.
- **Small repositories.** Under ~200 files the overhead competes with the benefit; the value is structural clarity, not compression.
- **Anything if the repo has no `.graphifyignore`.** Exclude `node_modules`, `dist`, `vendor`, build output and lockfiles before the first run. It is the difference between a 30-second build and a 10-minute one.

---

## Ponytail: Stop Writing Code You Do Not Need

Ask for a date picker and a default agent installs a library, writes a wrapper component, adds a stylesheet, and opens a discussion about timezones. Every one of those lines is output tokens now, and input tokens on every later turn that touches the file — forever. Over-building is the most expensive habit an agent has, and it is invisible in a token report.

Ponytail is not a prompt. It is a persistent seven-rung ladder the model climbs before writing anything:

```text
1. Does this need to exist?    → no: skip it (YAGNI)
2. Already in this codebase?   → reuse it, don't rewrite
3. Stdlib does it?             → use it
4. Native platform feature?    → use it
5. Installed dependency?       → use it
6. Can it be one line?         → one line
7. Only then: the minimum that works
```

Rung 2 is the anti-duplication rung, and it matters most in an existing codebase. Rung 4 produces the biggest wins — a date picker collapses from 404 lines to 23 because the browser already has `<input type="date">`.

Two design decisions: the ladder runs **after** the agent understands the problem, not instead of it. It reads the code the change touches and traces the real flow first — lazy about the solution, never about reading. And validation, error handling, security and accessibility are explicitly **off the chopping block**. That is the line between Ponytail and a bare "write one-liners" prompt, which cut cost similarly in the benchmark above while dropping a guard.

### Install Ponytail

```bash
# Claude Code — send these as TWO SEPARATE prompts
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

```bash
# Codex
codex plugin marketplace add DietrichGebert/ponytail
codex plugin add ponytail@ponytail
```

OpenCode reads `opencode.json`; Gemini, Cursor, Windsurf, Cline, Aider, Kiro, Zed and Copilot read a plain `AGENTS.md` from the repo root with zero setup, and the repository ships one. Node.js must be on your PATH for the lifecycle hooks; if `node` is missing the skills still work, the always-on activation just stays quiet.

> [!WARNING]
> **Install as a plugin, not as a bare `SKILL.md`.** JetBrains installed Ponytail as a plain skill file and let the model decide when to use it. Across ten sessions it self-activated **zero** times. Not rarely — never. The `SessionStart` hook is what injects the ruleset whether you ask or not. Copy the skill file into a skills folder and install nothing else, and you will measure exactly zero and conclude the tool does not work. Every number in the table above comes from the arm where the ruleset was actually injected.

### Commands

`/ponytail full` (default, ladder enforced), `/ponytail lite` (build it, name the lazier alternative), `/ponytail ultra`, `/ponytail off`, plus `/ponytail-review` for a delete-list on the current diff and `/ponytail-audit` for a repo-wide scan. Set a default in `~/.config/ponytail/config.json` with `{ "defaultMode": "full" }`, or via `PONYTAIL_DEFAULT_MODE`.

### What a real saving looks like

Two agents were asked to export a three.js scene to a Blender-ready OBJ. Both produced a file the verifier accepted. Both wrote the same fiddly loop, because three.js's `OBJExporter` cannot handle instanced meshes. The difference was everything around it.

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

Ten statements became five. Same geometry, same verifier score of 1.0. The agent rotated the object it already had instead of building a parent to rotate it for itself, and dropped an import on the way.

> [!NOTE]
> The cut concentrates where there is room to over-build. In the JetBrains run, code fell **31%** on large builds and moved by roughly **zero** on tasks that were already lean.

---

## Caveman: Shrink What the Agent Says

A default agent writes like a cover letter. Caveman makes it write like a field note. Same answer, no throat-clearing:

| Level | "Why does my React component re-render?" |
|---|---|
| Normal | The reason your component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using `useMemo`. **69 tokens** |
| `full` | New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`. **19 tokens** |

Code, commands, file paths and exact error strings are never touched.

That 69 → 19 is a 72% cut, and it is real. It is also **not** what happens in a coding session, because most tokens there are code and tool calls the style never reaches. The 65% headline belongs to chat-style Q&A.

### Install Caveman

One `npx` command. It works in 30+ agents, no account and no API key.

```bash
npx skills add JuliusBrussee/caveman -g
```

Set a default with `CAVEMAN_DEFAULT_MODE` or `~/.config/caveman/config.json`. `/caveman off` (or `normal mode`) turns it off.

### The proxy, which is the interesting part

The skill shrinks what the agent **says**. The proxy shrinks what the agent **reads** — logs, test output, JSON, diffs, search results — by running on your machine between the agent and the provider, with the originals kept in local SQLite and recoverable byte-for-byte.

```bash
npm install -g @caveman-ai/cli && caveman setup --install
caveman learn          # rank your token sinks worst-first
caveman shrink -- pnpm test
caveman trial -- claude   # A/B a real session, then: caveman trial report
```

Measured on a pinned 54-run suite, provider-reported input tokens, every answer checked against an exact oracle:

| Case | Direct | Through caveman | Change |
|---|--:|--:|--:|
| CSV outlier hunt | 165,823 | 74,484 | −55.1% |
| Log needle in haystack | 148,807 | 74,068 | −50.2% |
| YAML config drift | 132,124 | 71,027 | −46.2% |
| Test output failure | 150,377 | 108,514 | −27.8% |
| Deployment JSON drift | 147,975 | 108,939 | −26.4% |
| Dashboard HTML alert | 140,687 | 154,641 | **+9.9%** |
| **Total** | **885,793** | **591,673** | **−33.2%** |

The HTML row is red and it stays red: that case had no compression transform, so the proxy paid its own overhead and won nothing back.

> [!WARNING]
> The CLI sends anonymous usage stats by default — which commands ran and token counts through and cut. Never prompts, code or file paths. Turn it off with `caveman telemetry off` or `DO_NOT_TRACK=1`. Note the split licence: the skill and CLI are MIT, but the engine-linked runtime is BSL-1.1 source-available. If you need OSI-approved code in a commercial product, read `LICENSE` before deploying the proxy in production.

### When to skip Caveman

- You are billed **per request** rather than per token — GitHub Copilot premium requests, for example. A shorter answer is the same request.
- Your workload is **pure code generation** with no prose to cut.
- You are on terse one-liner Q&A, where the ~1,000-token-per-call tax can exceed the savings.

---

## Never Compress Your Own Prompts

This is the one finding worth repeating. The Adobe CAVEWOMAN paper measured both channels separately and found they point in opposite directions:

- Compressing the **model's output** cut realised cost 1.4–2.4× per model, up to 3× best case.
- Compressing the **human's input** raised net cost — ~1.15× on the five-benchmark mean, 2.7× under stronger compression — because models compensate with longer responses even as accuracy collapses.

So never let a tool rewrite *your* prompts into caveman-speak. Keep your prompts verbose and precise.

---

## Putting It Together

They do not overlap. The Caveman README puts it well: *Caveman shrinks what the agent says; Ponytail shrinks what it builds. Terse talk about minimal code.*

| Session moment | Tool | Job |
|---|---|---|
| Orient once per repo, or every 3–5 sessions | Graphify | "how does auth work? what is the blast radius?" |
| Start of every session | Ponytail, Caveman | keep the diff small, drop the prose |
| Unfamiliar ticket | Graphify | query the graph instead of grepping 200 files |
| Known ticket | Ponytail | check for an existing helper, then a native element |
| Before you commit | `/ponytail-review`, `/caveman-commit` | delete-list, one-line commit |

**Install in this order.** Ponytail first — two prompts, needs nothing but Node, has the only statistically significant saving, cannot break your build. Caveman's skill second — one `npx` command, free, reversible. Graphify third — the only one with a real build cost (~200k+ tokens) and a Python 3.10+ prerequisite, and it pays off only on repos large enough to make re-reading expensive. Caveman's proxy last, if at all — biggest single win on the reading side and also the biggest new component in your request path.

---

## Measure It Yourself

Every number here came from someone else's benchmark. Yours will differ, because your model, task mix and caching behaviour are yours. *That A/B outranks every number on the readme.*

Run the same ticket twice on the same model — once normally, once with the tools active — and diff the result against your provider's token report:

```bash
git diff --stat
git diff --numstat | awk '{ add += $1 } END { print add " lines added" }'
```

Pin the model, keep the task identical, and reset the session between runs. **Small samples lie in both directions**: a 10-task smoke run said Ponytail made things 9.6% *more* expensive with quality collapsing 0.51 → 0.31, while the full 80-task run said −10.3% cheaper. Read the distribution, not the mean — one long-context session can bill 25× normal and destroy an average.

And **"no quality difference detected" is not "quality unchanged."** That was a significance test, not a non-equivalence test; both this post and the source studies say so explicitly.

---

## Key Takeaways

- **Three leaks, three tools, no overlap.** Reading, writing and narrating are separate costs.
- **Ponytail first.** The only tool with a significant saving (−10.3%, p = 0.004). Expect ~10% cheaper, not 54% less code.
- **Caveman's style is small but harmless** — −8.5% output tokens, quality flat. Its *proxy* is the real win: −33.2% on the reading side.
- **Graphify is orientation, not implementation.** Build once, query when lost. Expect 5–10×, not 71.5×.
- **Never compress your own prompts.** Output compression cuts cost; input compression raises it.
- **Measure it yourself.** Every number above is someone else's benchmark, and small samples lie.

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
