# Chapter 06 — Shipping to Production: Solution

This folder contains the **complete, working solution** for Chapter 06. Use it as a reference or if you get stuck.

## Setup

```bash
pip install github-copilot-sdk pydantic httpx
```

## Configuration

Before running, set required environment variables:

```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_OWNER=microsoft
export GITHUB_REPO=vscode
export MODEL=gpt-4.1
export REPO_PATH=.
```

## Run

### Analyze a specific issue by number
```bash
python production_reviewer.py
```

The script will:
1. Fetch the issue from the GitHub API
2. Analyze it with your Issue Reviewer agent
3. Post a structured comment back to the issue
4. Log all steps with timestamps

### Expected Output

```
[14:23:15] [INFO] Fetching issue from GitHub...
[14:23:16] [INFO] Issue fetched: "Login crashes on mobile Safari"
[14:23:16] [INFO] Starting analysis with model gpt-4.1...
[14:23:18] [INFO] Tool call: get_file_contents on src/auth/login.js
[14:23:19] [INFO] Analysis complete!
[14:23:20] [INFO] Posting comment to GitHub...
[14:23:21] [INFO] Comment posted successfully!
```

## Key Concepts Demonstrated

- **Environment-based configuration** via `Config` class
- **GitHub REST API integration** with `httpx`
- **Structured logging** with timestamps and levels
- **Retry logic** with exponential backoff
- **Error handling** for transient failures
- **Production-grade schema validation** with Pydantic

## Files

| File | Description |
|------|-------------|
| `production_reviewer.py` | Complete, production-ready Issue Reviewer |

> 🎉 Congratulations! You've completed the course capstone.
