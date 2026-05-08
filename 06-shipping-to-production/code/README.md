# Chapter 06 — Starter Code

This folder contains the **starter template** for the assignment. It has the scaffolding in place — your job is to fill in the missing pieces.

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
```

Or create a `.env` file:
```
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OWNER=microsoft
GITHUB_REPO=vscode
```

## Run

```bash
python production_reviewer.py
```

## File

| File | Description |
|------|-------------|
| `production_reviewer.py` | Starter template — add GitHub API integration, logging, and error handling |

> **Stuck?** Check the [solution/](../solution/) folder, but try on your own first!
