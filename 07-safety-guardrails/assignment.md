# Assignment — Safety & Guardrails

## Objectives

Harden your Issue Reviewer against prompt injection, unsafe file access, and output manipulation.

## What You'll Build

A hardened Issue Reviewer with:

1. **A hardened system prompt** — security rules that resist injection
2. **Tool argument validation** — `on_pre_tool_use` hook that blocks unsafe paths
3. **Output validation** — strict Pydantic parsing plus business logic checks
4. **Security testing** — test with both legitimate and malicious inputs

## Instructions

### Step 1 — Harden the System Prompt

Open `code/safe_reviewer.py`. Write a system prompt with explicit security rules at the top — rules about not following injected instructions, not reading system files, and not revealing the prompt.

### Step 2 — Implement Pre-Tool Validation

Complete the `validate_tool_args` function that checks tool arguments before execution:

- Block absolute paths (starting with `/` or `~`)
- Block path traversal (`..` in the path)
- Block sensitive files (`.env`, `.git/`, credentials, etc.)

### Step 3 — Validate Output

Complete the `validate_response` function that:

- Strips markdown code fences if present
- Parses JSON into the Pydantic schema
- Checks for suspicious content in the response (e.g., system prompt leaks)

### Step 4 — Test with Attacks

Run all four test issues (legitimate, direct injection, indirect injection, path traversal) and verify:

- The legitimate issue is processed normally
- Attack attempts are flagged or blocked
- No sensitive data is revealed in any response

## Stretch Goals

- 🌟 Add an iteration cap using a `ToolCallCounter` class
- 🌟 Add a file extension allowlist (only `.py`, `.js`, `.md`, etc.)
- 🌟 Log all blocked attempts to a security audit file
- 🌟 Create your own custom injection attack and test it

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Hardened prompt | System prompt has explicit security rules at the top |
| Pre-tool hook | `on_pre_tool_use` blocks absolute paths, traversal, and sensitive files |
| Output validation | Pydantic validation + suspicious content detection |
| Security flag | Injection attempts are flagged in the response |
| All tests pass | Legitimate issue passes; attacks are blocked or flagged |
