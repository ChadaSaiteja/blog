---
layout: post
title: "Stop Guessing: Master AI Coding with Spec-Driven Development"
seo_title: "Spec-Driven Development with Spec Kit"
description: "A guide to Spec-Driven Development with GitHub Spec Kit: the workflow, setup for new and existing repos, every speckit command, and agent integrations."
date: 2026-10-05
updated: 2026-10-07
categories:
  - DevTools
  - AI
tags:
  - AI
  - GitHub
  - Spec-Kit
  - Software Engineering
author: "Saiteja Chada"
reading_time: "16 min read"
image: "/assets/og/spec-driven-development-guide.png"
keywords: "spec driven development, github spec kit, specify cli, ai coding agent, agentic sdd, speckit"
faq:
  - q: "What is Spec-Driven Development?"
    a: "Spec-Driven Development is the practice of writing down what a feature should do and why, before asking an AI agent to write any code. The written spec becomes the contract the agent builds against, instead of the agent inferring intent from a one-line prompt."
  - q: "What is GitHub Spec Kit?"
    a: "GitHub Spec Kit is a free, MIT-licensed toolkit from GitHub that makes Spec-Driven Development repeatable. It installs a command-line tool called specify and adds a set of slash commands to your AI coding agent, such as /speckit-specify, /speckit-plan and /speckit-converge."
  - q: "Do I have to rewrite my codebase to use Spec Kit?"
    a: "No. You run specify init --here --force inside an existing repository and apply it to the next single bounded change. Your application code is not modified; Spec Kit only adds a .specify directory and a folder of agent commands."
  - q: "Which AI coding agents does Spec Kit support?"
    a: "Spec Kit ships integrations for GitHub Copilot, Claude Code, Codex CLI, Gemini CLI and Cursor, plus a generic integration for anything else. You pick one with the --integration flag when you run specify init."
  - q: "What is the difference between specify and plan?"
    a: "The specify command writes what and why: user-visible behaviour, goals, and what must not break. The plan command writes how: the tech choices, which existing services to reuse, and where the change belongs in your architecture."
  - q: "What does /speckit-converge do?"
    a: "Converge compares the finished code against the spec, the plan and the task list. It never edits code. It either reports Converged, or it appends new tasks to tasks.md describing the gaps, so you can implement them and run it again."
howto:
  name: "Run one feature through the Spec-Driven Development workflow"
  description: "Install GitHub Spec Kit, write a feature spec, plan it against your existing code, and implement it with a convergence loop that checks the finished code against the spec."
  totalTime: "PT30M"
  steps:
    - name: "Install the CLI"
      text: "Run uv tool install specify-cli, then confirm it with specify version."
    - name: "Initialize in your repository"
      text: "In an existing repo run specify init --here --force --integration copilot. For a new project run specify init my-project --integration copilot."
    - name: "Set the project constitution once"
      text: "Run /speckit-constitution with rules that are already true for the repository, such as preserving public API compatibility and following existing service boundaries."
    - name: "Write the feature spec"
      text: "Run /speckit-specify and describe what the feature does, why it exists, and what must not break. Leave the tech stack out of this step."
    - name: "Close the gaps"
      text: "Run /speckit-clarify and answer the questions. These are product decisions and your answers are written back into spec.md."
    - name: "Plan it against your existing code"
      text: "Run /speckit-plan and tell the agent which existing services to reuse. Confirm the plan matches your current architecture and test style."
    - name: "Break the plan into tasks"
      text: "Run /speckit-tasks to produce an ordered tasks.md, then run /speckit-analyze to check the spec, plan and tasks agree."
    - name: "Implement the tasks"
      text: "Run /speckit-implement. For a large feature, name the phases to implement and ask it to stop before the rest."
    - name: "Converge against the spec"
      text: "Run /speckit-converge. If it appends new tasks to tasks.md instead of reporting Converged, run /speckit-implement again and repeat until it reports Converged."
---

Most developers hand an AI agent a one-line prompt and hope the code comes out
right. That approach &mdash; write a prompt, read the diff, fix what is wrong,
repeat &mdash; works surprisingly often, which is exactly the problem. It fails
quietly. The agent picks a plausible architecture that does not match yours, and
you only notice after reviewing forty files.

Spec-Driven Development inverts the order. You write down what you want first,
and the AI builds from that written spec.

This guide covers what SDD is, how to install GitHub Spec Kit, how to adopt it in
an existing codebase, what each command does, and how to point it at Copilot,
Claude Code or any other agent.

## What Is Spec-Driven Development?

Spec-Driven Development is a practice where the specification is written before
the code. The spec states **what** the feature does and **why** it exists. A
separate plan states **how** it will be built. The plan is broken into ordered
tasks, an AI agent implements those tasks, and then checks its own output against
the original spec.

The important part is the separation. In a normal AI session, product decisions
and technical decisions arrive tangled together, and the model quietly makes
both. Move the *what* out of the prompt and into a document you wrote, and the
decisions that belong to you stay yours.

Three concrete benefits follow from that:

- **Fewer wrong guesses.** The agent is not inferring your requirements from a
  sentence; it is reading them.
- **Decisions stay human.** Pricing rules, edge cases, and what must not break
  are written by you, not silently chosen by a language model.
- **Everything is reviewable.** Specs, plans and task lists are Markdown files in
  Git. They get code review, they get history, and they can be diffed.

**GitHub Spec Kit** is the free, MIT-licensed toolkit that makes this repeatable.
It installs a CLI called `specify` and adds ready-made commands to your agent.

## What Is the Spec-Driven Development Workflow?

The workflow is a chain of quality gates. Only the first two are load-bearing;
the rest exist to catch mistakes before they turn into code.

```text
constitution  (once per project)
      |
      v
specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge
            (optional)  (optional)           (optional)
```

| Step | Purpose |
|---|---|
| `constitution` | Project rules the AI must always follow. Once per project. |
| `specify` | Write the feature spec: what and why |
| `clarify` | The AI asks questions to remove ambiguity (optional) |
| `plan` | Technical plan: how it fits your existing code |
| `checklist` | "Unit tests for your requirements" (optional) |
| `tasks` | An ordered task list |
| `analyze` | Consistency check across spec, plan and tasks (optional) |
| `implement` | The AI writes the code |
| `converge` | Verify the code against the spec, and repeat until done |

`specify` is the only step strictly required before `plan`. Everything else is a
gate you can skip on a small change and should not skip on a large one.

> [!TIP]
> Running `clarify` is the highest-leverage optional step. Most wasted agent time
> comes from a gap in the spec that nobody noticed until after implementation.

## How Do You Install GitHub Spec Kit?

You need four things before you start: a recent Python, the `uv` package
manager, Git, and one supported AI coding agent. Installation itself is a single
command, and nothing in the toolkit needs to run inside your project. Do the
install once per machine and it is available in every repository you work in.

### Prerequisites

Before you begin, confirm the following are available:

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**, the Python package and tool manager
- **Git**
- One supported agent: GitHub Copilot, Claude Code, Codex CLI, Gemini CLI,
  Cursor, or anything else via the generic integration

### Install the Specify CLI

`uv tool install` puts `specify` on your path as an isolated tool, so it will
not interfere with your project's own Python dependencies:

```bash
uv tool install specify-cli
specify version      # confirm it works
```

To pin a specific release instead of tracking the latest, install straight from
the tagged source:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

Check which agents the installed version supports before you plan around one:

```bash
specify integration list
```

> [!NOTE]
> Spec Kit moves quickly and the command set has changed across releases. If a
> command in this guide does not exist, run `specify version` and compare against
> the official reference linked at the end of this post.

## Should You Adopt Spec Kit in an Existing Codebase?

You do not need to document your whole system first. The intended pattern is to
initialize Spec Kit in the repo you already have and use it for the next single
bounded change.

### Create a Baseline Branch First

Start from a clean tree on a dedicated branch, so every file Spec Kit adds shows
up in an ordinary code review:

```bash
cd your-existing-project
git checkout -b adopt-spec-kit
git status          # commit or stash any existing work first
```

This step is not ceremony. `--force` can replace files at paths Spec Kit manages,
and you want to be able to see exactly what it touched.

### Initialize in Place

```bash
specify init --here --force --integration copilot
```

The flags each do something specific:

- `--here` uses the current folder instead of creating a new one.
- `--force` permits a non-empty directory. It does not delete your app, but it
  may overwrite files at conflicting managed paths.
- `--integration copilot` selects your agent. See the agent table below.

Review the diff before committing. Spec Kit adds two things and changes nothing
else:

```text
your-project/
|-- .specify/
|   |-- memory/constitution.md   <- project rules
|   |-- templates/               <- spec, plan and tasks templates
|   `-- ...
`-- <agent folder>/              <- the commands for your agent
```

### Commit and Open the Agent in That Folder

```bash
git add .
git commit -m "Add Spec Kit"
```

Then open Copilot, Claude Code or whichever agent you chose **inside this
folder**. All `/speckit-*` commands are typed in the agent's chat, not in your
terminal. If the commands do not appear, the agent is almost certainly open in
the wrong directory.

## How Do You Start a Brand-New Project With Spec Kit?

With no existing code, the AI has nothing to read, so **you** choose the tech
stack during the `plan` step rather than letting the agent pick one for you.
This is the one situation where being specific about the stack is the whole
point of the plan step rather than an afterthought.

### Initialize the Project

Let Spec Kit create the directory:

```bash
specify init my-project --integration copilot
cd my-project
```

Or start from an empty folder or empty repository you created yourself:

```bash
mkdir my-project && cd my-project
specify init --here --integration claude
```

In non-interactive runs such as CI, Copilot is the default if you pass no
`--integration` flag at all.

### Set Up Git

The optional `git` extension handles initialization and feature branches:

```bash
specify extension add git
```

Or do it by hand, which is fine and more explicit:

```bash
git init
git add .
git commit -m "Initialize Spec Kit"
```

Push to GitHub when you are ready. Note that a GitHub `origin` remote is also
required later if you want to use `/speckit-taskstoissues`:

```bash
git remote add origin https://github.com/<you>/my-project.git
git push -u origin main
```

### Run the Workflow in a New Project

Type these in the agent's chat, one at a time, reviewing each result before
moving to the next:

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-clarify
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

For a project of any real size, add `checklist` and `analyze` between `plan` and
`tasks`, as shown in the workflow table earlier.

### New Repo Versus Existing Repo

The two setups differ in ways that matter more than the flags suggest:

| | New repository | Existing repository |
|---|---|---|
| Init command | `specify init my-project --integration <key>` | `specify init --here --force --integration <key>` |
| Before init | Nothing needed | Create a branch, commit or stash work |
| Constitution | Choose new principles freely | Use only rules already true for the repo |
| `plan` input | **You choose** the tech stack | Tell the AI to **reuse** existing architecture |
| Spec focus | Whole app or first feature | One bounded change, with "do not break" rules |

The constitution row is the one people get wrong. On an existing codebase, write
only rules that are already true. A constitution full of aspirations the repo does
not currently follow produces noise, not compliance.

## Which AI Agents Does Spec Kit Support?

Pick the integration key when you run `specify init`. The command prefix differs
per agent, which is the single most common source of confusion.

| Agent | Key | Where commands are installed | How you call a command |
|---|---|---|---|
| GitHub Copilot | `copilot` | `.github/skills/` | `/speckit-specify` |
| Claude Code | `claude` | `.claude/skills/` | `/speckit-specify` |
| Codex CLI | `codex` | `.agents/skills/` | `$speckit-specify` |
| Gemini CLI | `gemini` | `.gemini/commands/` | `/speckit.specify` |
| Cursor | `cursor-agent` | `.cursor/skills/` | `/speckit-specify` |
| Anything else | `generic` | Your own folder | Depends on the agent |

> [!NOTE]
> The spelling genuinely differs: `/speckit-specify`, `/speckit.specify` or
> `$speckit-specify`. Use the form your agent shows when you type its command
> prefix. The steps are identical either way.

Copilot uses skills by default. To get the older `.agent.md` / `.prompt.md`
layout instead, pass an integration option:

```bash
specify init --here --force --integration copilot --integration-options="--commands"
```

For an agent that is not on the list, point it at your own directory:

```bash
specify init --here --force --integration generic \
  --integration-options="--commands-dir .myagent/cmds"
```

### Using More Than One Agent

Teams rarely standardize on a single agent. You can add another later without
reinitializing:

```bash
specify integration install claude     # add a second agent
specify integration use claude         # make it the default
specify integration status             # check health
```

Three more commands are worth knowing. `specify integration switch <key>` swaps
the current agent, `specify integration upgrade` refreshes the commands after you
upgrade Spec Kit itself, and `specify integration uninstall` removes them while
keeping any files you edited.

## What Does Each Spec Kit Command Do?

The example running through this section is an existing e-commerce application
that needs **scheduled orders** added to it. Type each command in your agent's
chat, one at a time, and review the output before continuing.

### /speckit-constitution: Setting the Rules

Run this once per project. It writes the rules the agent must follow on every
later task, and outputs `.specify/memory/constitution.md`.

Use rules that are **already true** for your repo. Check your README, your CI
configuration and your architecture notes, and do not invent rules:

```text
/speckit-constitution Preserve public API compatibility. Follow the existing
service boundaries. Every database migration must include a rollback plan.
Run the repository's existing unit and integration tests.
```

### /speckit-specify: Writing the Feature Spec

Describe **what** you want and what must **not** break. Keep the tech stack out
of it entirely; that belongs to the next step. Output is a `spec.md` for the
feature, in its own feature folder:

```text
/speckit-specify Add scheduled order support. Customers can choose a future
date when creating an order. The date must be in the future and no more than
30 days ahead. Existing immediate orders must keep working. Scheduled orders
must not be processed before their date. Users can see the scheduled date.
```

The "must not break" clauses are the highest-value sentences you can write. They
are what stop the agent from refactoring something unrelated while it is in there.

### /speckit-clarify: Closing the Gaps

Optional, and usually worth running. The AI asks up to five questions about gaps
in the spec. **You** answer them, because these are product decisions, not
technical ones:

```text
/speckit-clarify Focus on date changes, holidays, and inventory reservation.
```

Typical questions look like: *Can users change the date later? What happens if
the date is a public holiday? Should inventory be reserved immediately?* Your
answers get written back into `spec.md`, so the record of what you decided is in
the same file as what you asked for.

### /speckit-checklist and /speckit-analyze: The Two Read-Only Gates

Both are optional and neither edits your code. `checklist` is best described as
unit tests for your requirements: it checks that the **spec** is complete and
unambiguous, not that the code is correct.

```text
/speckit-checklist Focus on scheduling rules and edge cases.
```

If it surfaces gaps, go back to `clarify` or `specify`. Tick each item only after
you have reviewed it, because the checklist is only useful if a human verifies
each line.

`analyze` cross-checks `spec.md`, `plan.md` and `tasks.md` against each other. It
never edits files. A typical finding looks like: *"the spec says scheduled orders
must not be processed early, but no task changes the scheduler."* Fix it at the
source, usually in `tasks`, then re-run until it is clean.

### /speckit-plan: Deciding How It Fits

This is where tech details go, and it is where the agent reads your **existing
code** to work out where the feature belongs:

```text
/speckit-plan Reuse the existing OrderService and the existing scheduler.
Add a scheduledAt field to the Order model. Keep the current test framework.
Do not change the existing JSON API response shape for immediate orders.
```

A typical result adds `Order.scheduledAt`, changes `createOrder()` and the
scheduler's pending-order filter, and adds validation for
`now < scheduledAt <= now + 30 days`.

**Check this output specifically:** does the plan reuse your current architecture,
libraries and test style? This is the step that decides whether SDD protects your
design or quietly replaces it.

### /speckit-tasks: Producing the Ordered List

No arguments needed. This creates `tasks.md`, an ordered list the agent will work
through:

```text
/speckit-tasks
```

Example output:

```text
T001 Add scheduledAt to Order model
T002 Add scheduled date validation
T003 Update create-order API
T004 Update OrderService
T005 Update scheduler filtering
T006 Update order response
T007 Add unit and integration tests
T008 Update API documentation
```

Because the list is a file, you can edit it. Reordering, splitting or deleting
tasks here is far cheaper than redirecting an agent mid-implementation.

### /speckit-implement: Writing the Code

The agent executes the tasks. For a small feature, run it once with no arguments:

```text
/speckit-implement
```

For a large feature, run it in stages and stop before it wanders:

```text
/speckit-implement Implement only the Setup and Foundational phases:
the Order model change and validation. Stop before the API changes.
```

Test each stage before starting the next one. Staged implementation turns one
risky long run into several small verifiable ones.

### /speckit-converge: Verifying Against the Spec

This is the command that makes the whole loop trustworthy. It compares the
finished code against the spec, the plan and the tasks, and it never edits code.
It does exactly one of two things:

- reports **Converged**, meaning nothing in the spec is missing, or
- **appends new tasks** to `tasks.md` describing each gap it found.

```text
/speckit-converge
```

If tasks were added, run `/speckit-implement` again, then `/speckit-converge`
again. Repeat until you actually see Converged rather than assuming you are
finished.

### /speckit-taskstoissues: Opening GitHub Issues

Optional. It turns `tasks.md` into GitHub issues, which is useful when you want
the work reviewed or assigned rather than executed in one pass. It needs a
GitHub `origin` remote and GitHub MCP tool access:

```text
/speckit-taskstoissues
```

## Which Steps Should You Use for Different Sized Work?

Not every change needs eight commands. Matching ceremony to size is what keeps
the process worth using at all:

| Work size | Steps |
|---|---|
| Large feature | specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge |
| Small feature | specify -> clarify -> plan -> tasks -> implement |
| Tiny change | specify -> implement |

Always run `plan` for anything meaningful in an existing codebase. The plan is
where the agent decides **where the feature belongs** in a system that already
exists, and skipping it is the most common way SDD turns into an expensive code
generator.

## What Does a Complete Setup and Shipping Checklist Look Like?

One-time setup:

1. Install Python 3.11+, uv, Git and an AI agent.
2. Run `uv tool install specify-cli` and confirm with `specify version`.
3. Existing repo: create a branch and commit or stash current work. New repo:
   skip this.
4. Existing repo: `specify init --here --force --integration <key>`. New repo:
   `specify init my-project --integration <key>`, then `cd my-project`.
5. Review the diff, then make the first commit.
6. Open your agent inside the project folder.
7. Run `/speckit-constitution` with rules that are already true for the repo.

Then, for every feature:

1. `/speckit-specify` with the what, the why, and what must not break.
2. `/speckit-clarify`, and answer the questions.
3. `/speckit-plan`, and confirm it fits the existing architecture.
4. `/speckit-checklist` for large features.
5. `/speckit-tasks`.
6. `/speckit-analyze`, and fix anything it reports.
7. `/speckit-implement`, in stages if the feature is large.
8. `/speckit-converge`, then repeat implement and converge until it reports
   Converged.
9. Review the code and the spec files together, then open a pull request.

## What Other Processes Does Spec Kit Include?

Spec Kit ships optional extensions for adjacent jobs, added only when you need
them:

```bash
specify extension add bug      # bug fixing: assess -> fix -> test
specify extension add assess   # evaluate an idea before building it
```

The bug workflow carries a slug so the three stages refer to the same report:

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

The `assess` extension is the one to reach for when you are not yet sure a feature
is worth specifying. Run it before `specify`, not after.

## What Are the Gotchas and Trade-offs?

Spec-Driven Development is a real improvement over prompt-and-pray, but it is not
free, and it has failure modes worth knowing before you rely on it.

- **It costs time on small changes.** A one-line CSS fix does not need eight
  commands. Use the tiny-change path and move on.
- **Specs go stale.** A feature folder is either a historical record or a living
  document; decide which as a team. Treating a year-old `spec.md` as current
  truth is how documentation rots.
- **The constitution must be realistic.** Rules the repo does not follow create
  noise, and noise trains you to skim past what matters.
- **Commands are typed in the agent's chat**, never in your terminal. Running
  `/speckit-specify` in a shell does nothing at all.
- **Missing commands usually mean the wrong folder.** Open the agent in the
  directory holding its command folder, then restart it.
- **Converge is not a proof.** It checks the code against the documents you wrote.
  If the spec was vague, a converged result is confidently wrong.

> [!IMPORTANT]
> Run one command at a time and read the output before continuing. The entire
> value of this process is the human reviewing each gate. Firing all eight
> commands in a row turns SDD back into prompt-and-pray with extra steps.

## Frequently Asked Questions

These are the questions that come up most often when people first run the
workflow. The answers are deliberately short, and each one points back to the
section above that covers it in full.

{% for item in page.faq %}
**{{ item.q }}**

{{ item.a }}

{% endfor %}

If your question is not answered here, the
[official Spec Kit reference](https://github.github.io/spec-kit/reference/agentic-sdd.html)
documents every command and flag, and it is kept current with each release.

## Key Takeaways

- **Write the spec before the prompt.** What and why belong to you; how belongs
  to the plan.
- **Adopt it on one bounded change.** You do not need to document your system
  first, and you should not try.
- **Never skip `plan` in an existing codebase.** It is the step that keeps your
  architecture instead of replacing it.
- **Loop until Converged.** `converge` appending tasks is the feature, not a bug.
- **Keep specs in Git.** They are the only durable record of why the code looks
  the way it does.
- **Match the process to the size of the change.** Eight commands for every diff
  is how the process gets abandoned.

## References

- [GitHub Spec Kit repository](https://github.com/github/spec-kit) &mdash; source
  code, releases and the changelog
- [Spec Kit guide: existing projects](https://github.github.io/spec-kit/guides/existing-projects.html)
  &mdash; official adoption guidance for an existing repo
- [Spec Kit reference: agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
  &mdash; full command reference
- [Spec Kit reference: integrations](https://github.github.io/spec-kit/reference/integrations.html)
  &mdash; supported agents and integration keys
- [uv documentation](https://docs.astral.sh/uv/) &mdash; the Python tool manager
  used to install the CLI
