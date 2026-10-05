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
reading_time: "12 min read"
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

1. **`constitution`**: Establish the foundational rules of your project.
2. **`specify`**: Write the high-level feature specification.
3. **`clarify`** (Optional): Use the AI to ask clarifying questions to remove ambiguity.
4. **`plan`**: Create a technical implementation plan that fits your existing architecture.
5. **`checklist`** (Optional): Generate a set of requirements-based unit tests.
6. **`tasks`**: Convert the plan into an ordered list of atomic tasks.
7. **`analyze`** (Optional): Run a consistency check across the spec, plan, and tasks.
8. **`implement`**: Execute the tasks.
9. **`converge`**: Verify the implementation against the original spec.

[!TIP]
Only `specify` is strictly required before moving to `plan`. The other steps act as optional quality gates to ensure higher confidence.

### The GitHub Spec Kit Toolkit

The toolkit is centered around the `specify` CLI. It manages your project's "memory" (like the `constitution.md`) and provides the bridge to your AI agent. It supports a wide variety of integrations, from GitHub Copilot and Claude Code to Cursor and Gemini.

## Deep Dive

### Setting Up Spec Kit

The setup process differs slightly depending on whether you are starting a new project or adopting the workflow in an existing repository.

#### Adopting an Existing Codebase

You do not need to document your entire system first. You can initialize Spec Kit inside your existing repo and apply it to the next bounded change.

1. **Create a baseline**: Create a new Git branch to ensure all Spec Kit additions are visible in your next pull request.
2. **Initialize**: Use the following command to install the kit into your current directory:
   ```bash
   specify init --here --force --integration copilot
   ```
   *Note: The `--force` flag allows initialization in a non-empty folder but may replace files at conflicting managed paths, so always use a clean branch.*
3. **Commit**: Add the new `.specify/` directory and the agent's skill folder to your repository.

#### Starting a Brand-New Project

When starting from scratch, you define the tech stack during the `plan` phase, as the AI has no existing code to reference.

1. **Initialize**:
   ```bash
   specify init my-new-project --integration claude
   cd my-new-project
   ```
2. **Add Git support**: You can use the built-in extension to manage your version control:
   ```bash
   specify extension add git
   ```

### Connecting Your AI Agent

The power of Spec Kit lies in how it communicates with your agent. Once initialized, you don't run these commands in your terminal; you type them directly into your agent's chat interface.

| Agent | Key | Command Prefix |
|---|---|---|
| GitHub Copilot | `copilot` | `/speckit-` |
| Claude Code | `claude` | `/speckit-` |
| Codex CLI | `codex` | `$speckit-` |
| Gemini CLI | `gemini` | `/speckit.` |
| Cursor | `cursor-agent` | `/speckit-` |

### A Worked Example: Adding Scheduled Orders

Imagine you are working on an existing e-commerce application and need to add a "scheduled orders" feature. Here is how the workflow looks in practice:

**Step 1: The Specification**
You tell the agent: `/speckit-specify Add scheduled order support. Customers can choose a future date...`

**Step 2: The Plan**
Instead of letting the AI guess, you guide it: `/speckit-plan Reuse the existing OrderService and scheduler. Add a scheduledAt field to the Order model.`

**Step 3: Implementation and Convergence**
After the agent writes the code via `/speckit-implement`, you run the most critical command:
`/speckit-converge`

The agent compares the code against the `spec.md` and `plan.md`. If it finds a gap—for example, if the spec requires a 30-day limit but the code doesn't enforce it—it will not say "Converged." Instead, it will append a new task to `tasks.md`. You then implement that task and run `converge` again until the state is clean.

## Gotchas and Trade-offs

While SDD significantly increases reliability, there are trade-offs to consider:

* **Increased Overhead**: For trivial changes (like fixing a typo or a single line of CSS), the full SDD lifecycle is overkill. Use a "Tiny change" workflow: `specify` $\rightarrow$ `implement`.
* **Maintenance of Specs**: As your project evolves, your specs may become stale. You must decide whether to treat `spec.md` as a living document or a historical record for each feature.
* **Agent-Specific Syntax**: Note that the prefix for commands varies (e.g., `/` vs `$`). Always check your agent's documentation or type `/` to see the available tools.

[!IMPORTANT]
Always run one command at a time. Review the AI's output at every stage before proceeding to the next. The strength of SDD is in the human-in-the-loop verification at every gate.

## Key Takeaways

* **Shift Left**: Move decision-making from the "implementation" phase to the "specification" phase.
* **Verifiable Intent**: Use the `converge` command to ensure the code actually does what the spec requires.
* **Architecture First**: Use the `plan` step to ensure AI-generated code respects your existing design patterns and libraries.
* **Version Controlled Wisdom**: Store your specs, plans, and constitutions in Git to build a searchable knowledge base for your codebase.

## References

* [GitHub Spec Kit Repository](https://github.com/github/spec-kit)
* [Spec Kit Guides: Existing Projects](https://github.github.io/spec-kit/guides/existing-projects.html)
* [Spec Kit Reference: Agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
