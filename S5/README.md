# Week 5 — The Hackathon: Vibe Coding a Production Simulator

## What This Week Is

**Summarize in 4-8 lines what Week 5 is about, how it connects to Weeks 1-4, and what the main objective is.**

---

## Part 1: Setting Up Claude Code

### Step 1 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

**If needed, include Node.js installation commands for your OS and a short note of what you actually used.**

```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS (Homebrew)
brew install node
```

### Verify Installation

```bash
claude --version
```

**Paste terminal output here.**

### Step 2 — Configure the API Endpoint

```bash
export ANTHROPIC_API_KEY="the-key-we-give-you"
export ANTHROPIC_BASE_URL="the-endpoint-we-give-you"
```

```bash
source ~/.bashrc   # or source ~/.zshrc
```

**Explain where you configured the variables and confirm you did not commit secrets.**

### Step 3 — Verify It Works

```bash
claude
```

**Describe what happened when you launched Claude Code and tested a simple prompt.**

### Step 4 — Learn the Basics

**List the Claude Code commands you tried (`/help`, `/status`, `/clear`, `/compact`, etc.) and what each one did in practice.**

---

## Part 2: The PRD-First Workflow

### Why a PRD?

**Explain why starting with a PRD is important for vibe coding in this project.**

### Team PRD Process

1. **Repository setup (`mkdir`, `git init`, etc.).**
2. **First prompt to Claude Code with project specification.**
3. **Clarifying questions discussed by the team.**
4. **Iterations and trade-off decisions.**
5. **Final PRD save location (`docs/PRD.md`).**

**Document what your team actually did at each step.**

### CLAUDE.md

**Show the final structure/content you used for `CLAUDE.md` (or summarize each section if you prefer).**

```markdown
# Project: 3D Printer Production Simulator
## What This Is
## Tech Stack
## Architecture
## Data Model
## Coding Conventions
## Current State
```

---

## Part 3: Project — 3D Printer Production Simulator

### Objective

**Restate the objective in your own words.**

### Functional Requirements (Minimum)

#### R0 — Initial Configuration
**Describe your implementation plan/evidence.**

#### R1 — Demand Generation
**Describe your implementation plan/evidence.**

#### R2 — Control Dashboard
**Describe your implementation plan/evidence.**

#### R3 — User Decisions
**Describe your implementation plan/evidence.**

#### R4 — Event Simulation
**Describe your implementation plan/evidence.**

#### R5 — Calendar Advance
**Describe your implementation plan/evidence.**

#### R6 — Event Log
**Describe your implementation plan/evidence.**

#### R7 — JSON Import/Export
**Describe your implementation plan/evidence.**

#### R8 — REST API
**Describe your implementation plan/evidence.**

### Non-Functional Requirements

- **Clean, commented code versioned with Git:**
- **Simple web interface:**
- **Cross-platform support:**

**Explain how you satisfy each one.**

---

## Session 5 Work Log

### Team Members

- **Name + role**
- **Name + role**
- **Name + role**

### What We Completed in This Session

**Bullet list of concrete outcomes from this kickoff session.**

### Blockers / Risks

**List current blockers, unknowns, or decisions still pending.**

### Plan Until Deadline

1. **Milestone 1:**
2. **Milestone 2:**
3. **Milestone 3:**

---

## Evidence (Screenshots / Terminal Logs)

### Claude Setup Evidence

**Add screenshots or pasted logs.**

### PRD Drafting Evidence

**Add screenshots or pasted logs.**

### Initial Project Run Evidence

**Add screenshots or pasted logs.**

---

## Required Reflection Questions

1. **How did your team use Claude Code effectively (and where did it fail)?**
2. **What decisions were made by the team vs. suggested by the model?**
3. **How did the PRD improve (or not improve) your implementation workflow?**
4. **What is your biggest technical risk for the final delivery?**
5. **What is your concrete next step after this session?**

---

## Repository

**GitHub repository link:**
