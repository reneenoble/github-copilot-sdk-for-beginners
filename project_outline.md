# 🏗️ Capstone Project Overview

## What You're Building

Across this course, you build a single project from scratch: an **AI-powered GitHub Issue Reviewer**.

By the final chapter, your agent will:

- **Read real GitHub issues** via the GitHub REST API
- **Analyze referenced source files** using tool calling
- **Classify difficulty** from Junior to Senior+ using a consistent rubric
- **Extract required concepts** and technologies
- **Provide mentoring advice** tailored to difficulty level
- **Stream progress** to the terminal in real-time
- **Post review comments** back to the issue as formatted Markdown
- **Defend against prompt injection** and path traversal attacks
- **Retry gracefully** on transient API failures

---

## How Each Chapter Builds the Reviewer

| Chapter | What You Add | Cumulative State |
|:-------:|-------------|-----------------|
| **00 — Getting Started** | Client, session, first prompt | Agent sends text; prints a plain-text summary |
| **01 — Structured Output** | Pydantic schema, JSON parsing | Agent returns validated `IssueReview` object |
| **02 — Prompt Engineering** | Rubric system prompt, few-shot examples | Classification is consistent and repeatable |
| **03 — Tool Calling** | `@define_tool`, file reader | Agent reads referenced source files |
| **04 — Agent Loop & Streaming** | Streaming events, `StatusReporter` | Terminal shows real-time tool calls and delta text |
| **05 — Safety & Guardrails** | Prompt hardening, pre-tool hook | Blocked path traversal and injection attempts |
| **06 — Shipping to Production** | GitHub API, logging, retry, test harness | Reads real issues; posts comments; handles failures |

---

## Project Architecture

```
GitHub Issue (title + body)
        │
        ▼
┌───────────────────────────────┐
│     GitHub Copilot SDK        │
│                               │
│  CopilotClient                │
│    └─ CopilotSession          │
│         ├─ System Prompt      │  ← Chapters 02, 05
│         ├─ Tools              │  ← Chapter 03
│         ├─ Streaming Events   │  ← Chapter 04
│         └─ Hooks              │  ← Chapter 05
└───────────────────────────────┘
        │
        ▼
   IssueReview (Pydantic)        ← Chapter 01
   { summary, difficulty_score,
     recommended_level,
     concepts_required,
     mentoring_advice,
     files_analyzed }
        │
        ▼
  Format as Markdown             ← Chapter 06
        │
        ▼
  Post to GitHub Issue           ← Chapter 06
```

---

## File Structure

Each chapter contributes a Python file that you build incrementally:

```
00-getting-started/
  code/issue_summary.py          ← starter template
  solution/issue_summary.py      ← completed reference

01-structured-output/
  code/issue_analysis.py
  solution/issue_analysis.py

02-prompt-engineering/
  code/reliable_classifier.py
  solution/reliable_classifier.py

03-tool-calling/
  code/tool_calling.py
  solution/tool_calling.py

04-agent-loop-streaming/
  code/streaming_reviewer.py
  solution/streaming_reviewer.py

05-safety-guardrails/
  code/safe_reviewer.py
  solution/safe_reviewer.py

06-shipping-to-production/
  code/production_reviewer.py    ← integrates everything
  solution/production_reviewer.py
```

Each `solution/` file is a complete, working implementation you can run immediately. Each `code/` file is a starter template with `# TODO` comments for you to fill in.

---

## Running the Final Reviewer

After completing Chapter 06, you can run the full reviewer against a real GitHub issue:

```bash
# Set required environment variables
export GITHUB_TOKEN=your_token
export GITHUB_OWNER=microsoft
export GITHUB_REPO=vscode
export ISSUE_NUMBER=1234

# Run the reviewer (prints the review, doesn't post)
python 06-shipping-to-production/solution/production_reviewer.py

# Post the review as a GitHub comment
export POST_COMMENT=true
python 06-shipping-to-production/solution/production_reviewer.py
```

---

## Quick Reference: SDK Patterns

| Pattern | Chapter | Code |
|---------|---------|------|
| Create a session | 00 | `await client.create_session(on_permission_request=PermissionHandler.approve_all, model="gpt-4.1")` |
| Send a prompt | 00 | `response = await session.send_and_wait("your prompt")` |
| Read the response | 00 | `if isinstance(response.data, AssistantMessageData): print(response.data.content)` |
| Define a tool | 03 | `@define_tool(description="...") async def my_tool(params: MyParams) -> str:` |
| Listen to events | 04 | `session.on(lambda event: ...)` |
| Pre-tool hook | 05 | `create_session(hooks={"on_pre_tool_use": validate_tool_args})` |
| Clean up | All | `await session.disconnect(); await client.stop()` |
