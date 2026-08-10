---
layout: post
title: "Running Free AI Coding Models in Your Terminal with OpenCode & Cloudflare"
description: "A complete step-by-step setup guide to connect OpenCode CLI with Cloudflare Workers AI using the free 10,000 Neurons/day quota."
date: 2026-08-10
categories:
  - AI
  - DevTools
tags:
  - opencode
  - cloudflare
  - llm
  - gemma
  - terminal
author: "Saiteja Chada"
reading_time: "5 min read"
draft: false
---

Terminal-based AI coding assistants like Claude Code have transformed developer workflows. However, running paid API models continuously can get expensive fast.

By leveraging **OpenCode** (a free, open-source terminal AI coding assistant) alongside **Cloudflare Workers AI**, you can run capable open models like **Gemma** completely free, backed by Cloudflare's official daily free tier allocation of **10,000 Neurons per day** (resetting daily at 00:00 UTC).

In this guide, we'll walk through installing OpenCode, retrieving Cloudflare API keys, selecting free-tier models like Gemma, understanding how Neurons work, and optimizing your daily usage.

---

## Free Tier vs. Paid Models: What You Need to Know

When configuring terminal AI tools on Cloudflare Workers AI:

- **Free Tier Models (e.g., Gemma)**: Open models like Google's Gemma series are natively hosted on Cloudflare Workers AI's free tier. They consume your daily **10,000 free Neurons**, enabling syntax generation, function refactoring, and code explanation without a credit card.
- **Paid / Frontier Models (GLM 5.2, Kimi 2.7, Claude)**: High-end agentic or long-context models like GLM 5.2 and Kimi 2.7 require paid API subscriptions or custom provider endpoints. For daily terminal coding at zero cost, open models on Cloudflare's free allocation are the ideal choice.

---

## Understanding Cloudflare's Neuron Quota

Cloudflare uses **Neurons** to measure the GPU compute required for AI inference:

- **Daily Free Limit**: **10,000 Neurons / day** for all users.
- **Reset Time**: Resets automatically every day at **00:00 UTC**.
- **Exceeding Limits**: On the Workers Free plan, requests pause until the next daily reset once 10,000 Neurons are consumed. On the Workers Paid plan, additional usage costs **$0.011 per 1,000 Neurons**.

---

## Step 1: Install OpenCode

Install OpenCode globally using your operating system's package manager:

### macOS / Linux
```bash
curl -fsSL https://opencode.ai/install | bash
```

### Windows
Choose your preferred package manager:
```bash
# Using Chocolatey
choco install opencode

# Using Scoop
scoop install opencode

# Using NPM
npm install -g opencode-ai
```

Verify your installation:
```bash
opencode --version
```

---

## Step 2: Retrieve Cloudflare API Credentials

1. Log into your dashboard at [dash.cloudflare.com](https://dash.cloudflare.com).
2. **Get your Account ID**:
   - Go to **AI** &rarr; **Workers AI** in the left sidebar.
   - Click **Use REST API**.
   - Copy your **Account ID**.
3. **Generate a Workers AI API Token**:
   - Go to **My Profile** &rarr; **API Tokens** &rarr; **Create Token**.
   - Select the pre-built **Workers AI** template (*do not use DNS or Edit Zone templates*).
   - Verify permissions are set to `Workers AI - Read + Edit`.
   - Click **Create Token** and copy the secret token.

---

## Step 3: Configure Cloudflare Provider in OpenCode

Now connect Cloudflare to OpenCode:

1. Launch OpenCode in your project directory:
   ```bash
   opencode
   ```
2. Open the model selector by typing:
   ```text
   /models
   ```
3. Press `Ctrl + A` to reveal all available AI providers.
4. Select **Cloudflare Workers AI**.
5. Paste your **Account ID** and **Workers AI API Token** when prompted.
6. Open `/models` again and select a free-tier open model like **Gemma**:
   - Select **Gemma** for fast terminal code generation, refactoring, and explanations.

---

## Step 4: Best Practices to Maximize Your 10,000 Daily Neurons

To get maximum coding value out of your 10,000 daily free Neurons:

- **Keep prompts focused**: State requirements clearly to save GPU compute and token overhead.
- **Reset session history**: Run `/reset` between unrelated tasks to prevent sending bloated prompt histories.
- **Use targeted context**: Direct OpenCode to specific files rather than inspecting large, irrelevant directories.

---

## Summary

Combining OpenCode with Cloudflare Workers AI gives you a terminal-native AI coding environment powered by open models like Gemma—100% free with **10,000 free Neurons every day**.
