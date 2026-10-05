---
layout: post
title: "Stop Guessing: Master AI Coding with Spec-Driven Development"
description: "Learn how to use Spec-Driven Development (SDD) and the GitHub Spec Kit to move from vague AI prompts to predictable, high-quality code implementation."
date: 2026-10-05
categories:
  - DevTools
tags:
  - AI
  - GitHub
  - Spec-Kit
  - Software Engineering
author: "Saiteja Chada"
reading_time: "15 min read"
---

Most developers treat AI agents like magic oracles, providing a vague prompt and hoping the resulting code aligns with their vision. This "prompt-and-pray" approach leads to hallucinations, architectural drift, and endless cycles of manual fixing. But what if you could flip the script: what if you defined the *what* and the *why* upfront, and let the AI handle the *how* under strict, verifiable constraints?

This is the core promise of Spec-Driven Development (SDD), and with the newly released GitHub Spec Kit, it is finally becoming a repeatable engineering process.

## Background

In a traditional AI-assisted workflow, the developer is often a reactive participant, correcting errors after they appear. Spec-Driven Development (SDD) transforms the developer into an architect. 

In SDD, the process is strictly tiered:
1. **The Spec:** Defines the behavior, goals, and constraints (the "what" and "why").
2. **The Plan:** Defines the technical implementation and architecture (the "how").
3. **The Tasks:** Breaks the plan into small, actionable, and verifiable steps.

By separating these concerns, you ensure that product decisions are made by you, not silently by an LLM. Furthermore, because everything is stored in Markdown files, your development intent is version-controlled and peer-reviewable in Git, just like your code.

## How It Works

GitHub Spec Kit is an open-source (MIT) toolkit that brings this tiered workflow to your local environment. It provides a command-line tool called `specify` and installs specialized "skills" (agentic commands) into your favorite AI coding agent.

### The SDD Lifecycle

The workflow follows a logical progression of quality gates. While you can skip some steps for tiny changes, a robust feature implementation typically follows this path:

| Step | Purpose |
|---|---|
| `constitution` | Project rules the AI must always follow (once per project) |
| `specify` | Write the feature spec (what + why) |
| `clarify` | AI asks questions to remove ambiguity (optional) |
| `plan` | Technical plan: how it fits your existing code |
| `checklist` | "Unit tests for your requirements" (optional) |
| `tasks` | Ordered task list |
| `analyze` | Consistency check across spec, plan, tasks (optional) |
| `implement` | AI writes the code |
| `converge` | Verify code against the spec; repeat until done |

Only `specify` is strictly required before moving to `plan`. The other steps act as optional quality gates to ensure higher confidence.

## Deep Dive

### Setting Up Spec Kit

#### Prerequisites

Before you begin, ensure you have the following:
- **Python 3.11+**
- [**uv**](https://docs.astral.sh/uv/) (Python package tool)
- **Git**
- One supported AI coding agent (GitHub Copilot, Claude Code, Codex, Gemini CLI, Cursor, etc.)

#### Installing the CLI

Install the `specify` CLI using `uv`:

```bash
uv tool install specify-cli
specify version      # confirm it works
```

To pin a specific release instead:
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

#### Integrating with Your Existing Codebase

You do **not** need to document your whole system first. You initialize Spec Kit inside your repo and use it for the **next bounded change**.

1. **Create a safe baseline**: 
   ```bash
   git checkout -b adopt-spec-kit
   ```
2. **Initialize in place**:
   ```bash
   specify init --here --force --integration copilot
   ```
   *Note: `--force` allows initialization in a non-empty folder, but it can replace files at conflicting managed paths.*
3. **Review the diff**: Spec Kit adds a `.specify/` directory for memory and templates, and an `<agent folder>/` for your agent's skills.
4. **Commit and Launch**: Commit the changes and open your agent (Copilot, Claude Code, etc.) **inside this folder**.

#### Starting a Brand-New Repository

When there is no code yet, you decide the tech stack in the `plan` step.

1. **Initialize**:
   ```bash
   specify init my-project --integration copilot
   cd my-project
   ```
2. **Set up Git**:
   ```bash
   specify extension add git
   ```

| | New repository | Existing repository |
|---|---|---|
| **Init command** | `specify init my-project --integration <key>` | `specify init --here --force --integration <key>` |
| **Before init** | Nothing needed | Create a branch, commit or stash work |
| **Constitution** | Choose new principles freely | Use only rules already true for the repo |
| **`plan` input** | **You choose** the tech stack | Tell the AI to **reuse** existing architecture |
| **Spec focus** | Whole app or first feature | One bounded change, with "do not break" rules |

### Connecting to AI Agents

Pick the integration key when you run `specify init`. The commands are then called directly in your agent's chat.

| Agent | Key | Where commands are installed | How you call a command |
|---|---|---|---|
| GitHub Copilot | `copilot` | `.github/skills/` | `/speckit-specify` |
| Claude Code | `claude` | `.claude/skills/` | `/speckit-specify` |
| Codex CLI | `codex` | `.agents/skills/` | `$speckit-specify` |
| Gemini CLI | `gemini` | `.gemini/commands/` | `/speckit.specify` |
| Cursor | `cursor-agent` | `.cursor/skills/` | `/speckit-specify` |

> [!NOTE]
> The spelling differs by agent (e.g., `/`, `$`, or `.`). Use the form your agent shows when you type the prefix.

### Command Reference

Here is a breakdown of the core commands you will use in your agent's chat.

#### `/speckit-constitution`
Sets the rules the AI must follow (e.g., "Follow existing service boundaries"). Output: `.specify/memory/constitution.md`.

#### `/speckit-specify`
Describe **what** you want and what must **not** break. No tech stack here. Output: `spec.md`.

#### `/speckit-clarify` (Optional)
The AI asks up to five questions about gaps. You answer them, and these are written back into `spec.md`.

#### `/speckit-plan`
This is where tech details go. The AI studies your **existing code** to decide where the feature belongs.

#### `/speckit-checklist` (Optional)
Generates a "unit test" for your requirements. It checks if the **spec** is complete, not the code.

#### `/speckit-tasks`
Creates an ordered `tasks.md` file (e.g., `T001 Add field to model`, `T002 Update API`).

#### `/speckit-analyze` (Optional)
A read-only check to ensure `spec.md`, `plan.md`, and `tasks.md` are consistent.

#### `/speckit-implement`
The AI executes the tasks. For large features, you can run this in stages (e.g., "Implement only the foundational phases").

#### `/speckit-converge`
The most critical step. It compares the finished code with the spec and plan. It either reports **Converged** or **appends new tasks** to `tasks.md` for the gaps. Repeat until clean.

#### `/speckit-taskstoissues` (Optional)
Turns `tasks.md` into GitHub issues (requires GitHub MCP tool access).

### Extensions

Spec Kit also includes specialized workflows for common tasks:

- **Bug Fixing**: 
  ```text
  /speckit-bug-assess "Description of bug"
  /speckit-bug-fix slug=bug-id
  /speckit-bug-test slug=bug-id
  ```
- **Idea Assessment**: Use `specify extension add assess` to evaluate ideas before building.

## Practical Guide

### Which Steps to Use?

| Work size | Steps |
|---|---|
| **Large feature** | `specify` $\rightarrow$ `clarify` $\rightarrow$ `plan` $\rightarrow$ `checklist` $\rightarrow$ `tasks` $\rightarrow$ `analyze` $\rightarrow$ `implement` $\rightarrow$ `converge` |
| **Small feature** | `specify` $\rightarrow$ `clarify` $\rightarrow$ `plan` $\rightarrow$ `tasks` $\rightarrow$ `implement` |
| **Tiny change** | `specify` $\rightarrow$ `implement` |

### Full Implementation Checklist

1. **Setup**: Install `specify-cli`, initialize with `--integration <key>`, and set your `constitution`.
2. **Feature Start**: Run `specify` $\rightarrow$ `clarify` $\rightarrow$ `plan`.
3. **Verification**: Run `tasks` $\rightarrow$ `analyze` $\rightarrow$ `implement`.
4. **Closing the Loop**: Run `converge`. If tasks are added, repeat `implement` $\rightarrow$ `converge`.
5. **Shipping**: Review code and spec files together, then open a PR.

## Gotchas and Trade-offs

* **Increased Overhead**: For trivial changes, the full cycle is overkill. Use the "Tiny change" workflow.
* **Maintenance**: Spec files can age. Decide if they are living documents or historical records.
* **Command Syntax**: Always verify if your agent uses `/`, `$`, or `.` prefixes.

[!IMPORTANT]
Always run one command at a time. Review the AI's output at every stage before proceeding. The strength of SDD is in the human-in-the-loop verification at every gate.

## Key Takeaways

* **Shift Left**: Move decisions from implementation to specification.
* **Verifiable Intent**: Use `converge` to ensure code matches the spec.
* **Architecture First**: Use `plan` to ensure the AI respects your existing design.
* **Version Controlled Wisdom**: Store your specs in Git to build a knowledge base.

## References

* [GitHub Spec Kit Repository](https://github.com/github/spec-kit)
* [Spec Kit Guides: Existing Projects](https://github.github.io/spec-kit/guides/existing-projects.html)
* [Spec Kit Reference: Agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
