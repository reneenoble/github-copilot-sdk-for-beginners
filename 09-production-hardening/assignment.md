# Assignment — Production Hardening & GitHub Integration

## Objectives

Connect the Issue Reviewer to the GitHub API, add logging, error handling, and ship it.

## What You'll Build

A production-ready Issue Reviewer that:

1. **Fetches** GitHub issues via the REST API
2. **Reviews** the issue using the Copilot SDK
3. **Posts** a formatted Markdown comment on the issue
4. **Applies** a difficulty label
5. **Logs** key events with structured logging
6. **Retries** on transient failures

## Instructions

### Step 1 — Set Up Configuration

Open `code/production_reviewer.py`. Complete the `Config` class that reads from environment variables: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `MODEL`, and `REPO_PATH`.

### Step 2 — Implement GitHub API Calls

Complete the `fetch_issue`, `post_comment`, and `add_labels` functions using `httpx` with the authenticated headers.

### Step 3 — Format the Review

Complete the `format_review_comment` function to produce a GitHub-flavored Markdown comment with the review summary, difficulty bar, concepts, and mentoring advice.

### Step 4 — Add Logging

Use Python's `logging` module. Log tool calls, decisions, errors, and timing.

### Step 5 — Wire It All Together

Complete the `review_issue` function that:

1. Fetches the issue from GitHub
2. Runs the SDK review
3. Parses the response
4. Posts the comment
5. Applies the label

### Step 6 — Test It

Run the reviewer against a real issue in one of your repositories:

```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_OWNER="your-username"
export GITHUB_REPO="your-repo"
python production_reviewer.py 1
```

## Stretch Goals

- 🌟 Add retry logic with exponential backoff (1s, 2s, 4s...)
- 🌟 Create a GitHub Action workflow that triggers the reviewer on `issues.opened` events
- 🌟 Track total token usage per review (character count as proxy)
- 🌟 Add a `--dry-run` flag that reviews without posting
- 🌟 Support batch mode: review all open issues with `python production_reviewer.py --all`

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Config from env | All settings read from environment variables with validation |
| GitHub API | Issue is fetched, comment is posted, label is applied |
| Formatted comment | Review is rendered as readable GitHub Markdown |
| Logging | Key events (tool calls, errors, timing) are logged |
| Error handling | Failures are caught and reported without crashing |
| End-to-end test | At least one real issue reviewed successfully |
