# Assignment — Shipping to Production

## Objectives

Connect your Issue Reviewer to the real GitHub API, add production-grade logging and error handling, and deploy a test harness that verifies everything works end-to-end.

## What You'll Build

A production-ready Issue Reviewer that:

1. **Fetches real issues** — reads issues from a GitHub repository via the REST API
2. **Posts review comments** — writes structured review comments back to the issue
3. **Uses environment configuration** — reads settings from environment variables, not hardcoded values
4. **Logs everything** — structured logging for debugging and observability
5. **Handles errors gracefully** — retry logic with exponential backoff for transient failures
6. **Passes a test harness** — a simple validation script that confirms correct behavior

## Instructions

### Step 1 — Set Up Environment Configuration

Configure your script to read settings from environment variables:

- `GITHUB_TOKEN` — your personal access token with `repo` scope
- `GITHUB_OWNER` — the repository owner (e.g., `microsoft`)
- `GITHUB_REPO` — the repository name (e.g., `vscode`)

Validate that all required variables are set, and provide clear error messages if they're missing.

### Step 2 — Fetch Issues from GitHub

Use `httpx` to fetch a real issue from the GitHub API. Your `fetch_issue()` function should:

- Make an authenticated GET request to `/repos/{owner}/{repo}/issues/{number}`
- Handle HTTP errors (401, 403, 404) with clear messages
- Return the issue title and body for your reviewer

### Step 3 — Format and Post Reviews

Complete the `format_review_comment()` function that converts your structured `IssueReview` into a GitHub-flavored Markdown comment. Then implement `post_comment()` to write it back to the issue.

### Step 4 — Add Structured Logging

Replace `print()` statements with Python's `logging` module:

- Log at `INFO` level for each processing step
- Log at `WARNING` for non-fatal issues (e.g., missing fields)
- Log at `ERROR` for failures (API errors, validation errors)
- Include timestamps and context in log messages

### Step 5 — Implement Retry Logic

Wrap your API calls in retry logic with exponential backoff:

- Retry on transient errors (429, 500, 502, 503)
- Don't retry on permanent errors (401, 403, 404)
- Cap at 3 attempts with increasing wait times

### Step 6 — Build a Test Harness

Create a simple test script that:

- Fetches a known issue from a test repository
- Runs your reviewer on it
- Validates the structured output against expected fields
- Reports pass/fail for each check

## Stretch Goals

- 🌟 Process multiple issues in batch (e.g., all open issues with a specific label)
- 🌟 Add a `--dry-run` flag that formats the review but doesn't post it
- 🌟 Track and log token usage per review to monitor costs
- 🌟 Add a GitHub Action workflow that triggers the reviewer on new issues

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Environment config | All settings read from env vars; clear error for missing values |
| API integration | Fetches issues and posts comments successfully |
| Markdown formatting | Review comment is well-formatted with emoji, scores, and sections |
| Logging | Uses `logging` module with appropriate levels and context |
| Error handling | Retries transient errors; fails gracefully on permanent errors |
| Test harness | Test script validates output and reports results clearly |
