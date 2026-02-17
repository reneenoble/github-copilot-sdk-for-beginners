# Chapter 06 — Shipping to Production

![Chapter 06 banner illustration — the Issue Reviewer shipping to production connected to GitHub](./images/banner.png)

<!-- TODO: Add banner image to ./06-shipping-to-production/images/banner.png — An illustration (1280×640) showing a rocket launching (representing shipping to production). The rocket is labeled "Issue Reviewer" and trails connect to GitHub's octocat, a logging dashboard, and retry arrows. On the right, a GitHub issue shows an auto-posted comment with the structured review. Same art style as course. -->

> **Building it is half the work. Shipping it is the other half.**

You've built a powerful Issue Reviewer with structured output, tool calling, streaming, and safety guardrails. But it's still running on your laptop with hardcoded test data. This final chapter teaches you to **ship it to production** — connecting to the real GitHub API, adding logging and error handling, and making your reviewer ready for the real world.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 05: Safety & Guardrails](../05-safety-guardrails/README.md)** first. You'll also need a GitHub personal access token and `pip install httpx` for async HTTP requests.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Connect to the GitHub API to read issues and post comments
- Format structured reviews as GitHub-flavored Markdown
- Add environment-based configuration
- Implement structured logging
- Handle errors gracefully with retries
- Create a simple test harness for your agent

> ⏱️ **Estimated Time**: ~45 minutes (15 min reading + 30 min hands-on)

---

# Shipping Your Agent

## 🧩 Real-World Analogy: Opening a Restaurant vs. Cooking at Home

<img src="./images/analogy-restaurant.png" alt="Home kitchen vs professional restaurant kitchen" width="800"/>

<!-- TODO: Add analogy image to ./06-shipping-to-production/images/analogy-restaurant.png — A split illustration: left side shows a developer happily cooking in a cozy home kitchen ("works on my machine"); right side shows a professional restaurant kitchen with order tickets, logging screens, fire suppression systems, and delivery trucks ("production"). Same art style as course. -->

You've been cooking great meals at home. Your friends love the food. Now you want to open a restaurant. Same recipes, same skills — but suddenly you need a whole new layer of concerns:

| Cooking at Home | Opening a Restaurant | Production Hardening |
|---|---|---|
| Ingredients from your fridge | Supplier deliveries, inventory | **GitHub API integration** — fetch real issues |
| Serve on any plate | Professional plating | **Formatted Markdown comments** — structured output |
| Adjust seasoning by taste | Standardized recipes | **Environment config** — settings from env vars |
| No receipts needed | Transaction records | **Structured logging** — record every step |
| If something burns, start over | Can't close for every mistake | **Retry logic** — handle transient failures |
| Cook one dish at a time | Quality control on every order | **Test harness** — verify it works before serving |

The food itself didn't change. What changed is everything *around* it — the infrastructure that makes it reliable and ready for real customers.

---

# Key Concepts

## GitHub API Integration

Use `httpx` for async HTTP calls to the GitHub API:

```python
import httpx
import os

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Fetch an issue from the GitHub API."""
    async with httpx.AsyncClient() as client:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def post_comment(owner: str, repo: str, issue_number: int, body: str):
    """Post a comment on a GitHub issue."""
    async with httpx.AsyncClient() as client:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = await client.post(url, headers=HEADERS, json={"body": body})
        response.raise_for_status()
        return response.json()
```

---

## Formatting Reviews as Markdown

Convert the structured review into a readable GitHub comment:

```python
def format_review_comment(review: IssueReview) -> str:
    """Format a review as a GitHub Markdown comment."""
    level_emoji = {"Junior": "🟢", "Mid": "🟡", "Senior": "🟠", "Senior+": "🔴"}
    emoji = level_emoji.get(review.recommended_level, "⚪")
    bar = "█" * review.difficulty_score + "░" * (5 - review.difficulty_score)
    concepts = "\n".join(f"  - {c}" for c in review.concepts_required)

    return f"""## 🤖 AI Issue Review

**Summary**: {review.summary}

### Difficulty Assessment
| Metric | Value |
|--------|-------|
| Score | {bar} {review.difficulty_score}/5 |
| Level | {emoji} {review.recommended_level} |

### Required Concepts
{concepts}

### 💡 Mentoring Advice
{review.mentoring_advice}

---
<sub>Generated by AI Issue Reviewer • Powered by GitHub Copilot SDK</sub>
"""
```

---

## Environment Configuration

Use environment variables for all configurable values:

```python
import os

class Config:
    """Application configuration from environment variables."""
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_OWNER: str = os.environ.get("GITHUB_OWNER", "")
    GITHUB_REPO: str = os.environ.get("GITHUB_REPO", "")
    MODEL: str = os.environ.get("MODEL", "gpt-4.1")
    REPO_PATH: str = os.environ.get("REPO_PATH", ".")

    @classmethod
    def validate(cls):
        required = ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO"]
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
```

---

## Structured Logging

Add logging for observability:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("issue-reviewer")

# Use in your code:
logger.info("Fetching issue #%d", issue_number)
logger.info("Tool call: %s", tool_name)
logger.error("Failed to post comment: %s", error)
```

---

## Error Handling & Retries

Wrap API calls with retry logic:

```python
import asyncio

async def with_retry(func, *args, max_retries: int = 3, delay: float = 1.0):
    """Run an async function with exponential backoff retries."""
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = delay * (2 ** attempt)
            logger.warning("Attempt %d failed: %s. Retrying in %.1fs...",
                          attempt + 1, e, wait)
            await asyncio.sleep(wait)
```

---

## Simple Test Harness

Create golden test cases to verify your reviewer works:

```python
GOLDEN_TESTS = [
    {
        "name": "Typo fix",
        "issue": "Title: Fix typo\n\nChange 'recieve' to 'receive' in README.md.",
        "expected_score": 1,
        "expected_level": "Junior",
    },
    {
        "name": "Security vulnerability",
        "issue": "Title: SQL injection in search\n\nThe search endpoint passes user input directly to SQL without parameterization.",
        "expected_score": 4,
        "expected_level": "Senior",
    },
]


async def run_tests(client):
    """Run golden tests and report results."""
    passed = 0
    for test in GOLDEN_TESTS:
        review = await run_review(client, test["issue"])
        score_ok = abs(review.difficulty_score - test["expected_score"]) <= 1
        level_ok = review.recommended_level == test["expected_level"]
        
        if score_ok and level_ok:
            print(f"✅ {test['name']}")
            passed += 1
        else:
            print(f"❌ {test['name']}: got {review.difficulty_score}/{review.recommended_level}")
    
    print(f"\n{passed}/{len(GOLDEN_TESTS)} tests passed")
```

---

# See It In Action

Here's the complete production reviewer. Create `production_reviewer.py`:

```python
import asyncio
import json
import logging
import os
from datetime import datetime
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
from typing import Literal
import httpx


# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("issue-reviewer")


# --- Config ---
class Config:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
    MODEL = os.environ.get("MODEL", "gpt-4.1")
    REPO_PATH = os.environ.get("REPO_PATH", ".")

    @classmethod
    def validate(cls):
        missing = [k for k in ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO"] 
                   if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")


# --- Schema ---
class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str
    files_analyzed: list[str] = Field(default_factory=list)


# --- GitHub API ---
GITHUB_API = "https://api.github.com"


async def github_request(method: str, url: str, **kwargs) -> dict:
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()


async def fetch_issue(issue_number: int) -> dict:
    url = f"{GITHUB_API}/repos/{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}/issues/{issue_number}"
    return await github_request("GET", url)


async def post_comment(issue_number: int, body: str):
    url = f"{GITHUB_API}/repos/{Config.GITHUB_OWNER}/{Config.GITHUB_REPO}/issues/{issue_number}/comments"
    return await github_request("POST", url, json={"body": body})


# --- Tool ---
class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    full_path = os.path.realpath(os.path.join(Config.REPO_PATH, params.file_path))
    if not full_path.startswith(os.path.realpath(Config.REPO_PATH)):
        return "Error: Access denied"
    try:
        with open(full_path, "r") as f:
            return f.read()[:10_000]
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"


# --- Formatting ---
def format_review_comment(review: IssueReview) -> str:
    emoji = {"Junior": "🟢", "Mid": "🟡", "Senior": "🟠", "Senior+": "🔴"}.get(
        review.recommended_level, "⚪")
    bar = "█" * review.difficulty_score + "░" * (5 - review.difficulty_score)
    concepts = "\n".join(f"  - {c}" for c in review.concepts_required)
    
    return f"""## 🤖 AI Issue Review

**Summary**: {review.summary}

| Metric | Value |
|--------|-------|
| Score | {bar} {review.difficulty_score}/5 |
| Level | {emoji} {review.recommended_level} |

**Required Concepts**: {concepts}

**💡 Mentoring Advice**: {review.mentoring_advice}

---
<sub>Generated by AI Issue Reviewer</sub>
"""


# --- Main ---
SYSTEM_PROMPT = """You are a GitHub issue reviewer. Analyze the issue and respond with ONLY JSON:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<specific skill>", ...],
  "mentoring_advice": "<guidance>",
  "files_analyzed": ["<files you read>"]
}

Difficulty: 1=typo/docs, 2=simple bug, 3=feature, 4=cross-cutting, 5=architecture."""


async def review_issue(client, issue_number: int):
    """Fetch, review, and comment on a GitHub issue."""
    logger.info("Fetching issue #%d", issue_number)
    issue = await fetch_issue(issue_number)
    issue_text = f"Title: {issue['title']}\n\n{issue['body'] or ''}"

    logger.info("Creating review session")
    session = await client.create_session({
        "model": Config.MODEL,
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
        "tools": [get_file_contents],
    })

    response = await session.send_and_wait({"prompt": f"Review this issue:\n\n{issue_text}"})
    review = IssueReview.model_validate_json(response.data.content)

    logger.info("Posting comment to issue #%d", issue_number)
    comment = format_review_comment(review)
    await post_comment(issue_number, comment)

    await session.destroy()
    return review


async def main():
    Config.validate()
    
    client = CopilotClient()
    await client.start()

    # Review a specific issue (pass as command line arg or hardcode)
    import sys
    issue_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    review = await review_issue(client, issue_number)
    print(f"\n✅ Review posted for issue #{issue_number}")
    print(f"   Difficulty: {review.difficulty_score}/5 ({review.recommended_level})")

    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export GITHUB_TOKEN="your-token"
export GITHUB_OWNER="your-username"
export GITHUB_REPO="your-repo"
python production_reviewer.py 42  # Review issue #42
```

<details>
<summary>🎬 See it in action!</summary>

![Production Reviewer Demo](./images/production-demo.gif)

<!-- TODO: Add GIF showing: (1) script runs, (2) logs show fetching issue, (3) review is generated, (4) comment posted, (5) GitHub shows the formatted comment. -->

*Demo output varies. Your results will differ from what's shown here.*

</details>

---

# Practice

<img src="../images/practice.png" alt="Warm desk setup ready for hands-on practice" width="800"/>

Time to ship your Issue Reviewer!

---

## ▶️ Try It Yourself

1. **Test locally first** — Run the reviewer against a real issue in one of your repos

2. **Add label automation** — Extend `review_issue` to also add a difficulty label (e.g., "good first issue" for score 1)

3. **Create a test harness** — Add 3-5 golden test cases and run them before deploying

4. **Add streaming output** — Show progress in the terminal while the review runs

---

## 📝 Assignment

### Main Challenge: Deploy Your Issue Reviewer

Create a production-ready Issue Reviewer that:

1. Connects to the GitHub API to fetch real issues
2. Runs your hardened agent with all guardrails
3. Formats the review as a Markdown comment
4. Posts the comment back to the issue
5. Includes basic logging and error handling

**Success criteria**: Run `python production_reviewer.py <issue-number>` and see a formatted review comment appear on the GitHub issue.

**Stretch goals**:
- Add a GitHub Action that runs on new issues
- Add difficulty labels automatically
- Track token usage and costs

<details>
<summary>💡 Hints</summary>

**GitHub token**: Create at https://github.com/settings/tokens with `repo` scope

**Testing locally**: Start with a test issue in a repo you own

**Common issues:**
- 401 errors: Token missing or expired
- 404 errors: Wrong owner/repo name
- 422 errors: Issue doesn't exist

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Missing GITHUB_TOKEN | 401 Unauthorized | Export the token as env var |
| Wrong repo name | 404 Not Found | Check GITHUB_OWNER and GITHUB_REPO |
| No repo scope on token | 403 Forbidden | Regenerate token with `repo` scope |
| JSON parsing fails | ValidationError | Check the model's raw response for issues |

### Troubleshooting

**"401 Unauthorized"** — Your GitHub token is missing or invalid. Make sure `GITHUB_TOKEN` is exported and the token hasn't expired.

**"Comment doesn't appear"** — Check the GitHub API response. You might not have write access to the repo.

**"Review is wrong"** — Run your test harness to verify the agent. The issue might be ambiguous.

</details>

---

# Summary

## 🔑 Key Takeaways

1. **Environment configuration** — never hardcode tokens or settings; use environment variables
2. **Structured logging** — record what's happening for debugging and observability
3. **Error handling with retries** — transient failures are normal; handle them gracefully
4. **Format for humans** — convert structured data to readable Markdown for GitHub comments
5. **Test before shipping** — a simple test harness catches problems before users do

> 📚 **Glossary**: New to terms like "retry" or "environment variable"? See the [Glossary](../GLOSSARY.md) for definitions.

---

## 🏗️ Capstone Complete! 🎉

You've built a production-ready AI GitHub Issue Reviewer!

| Chapter | Feature | Status |
|---------|---------|--------|
| 00 | Basic SDK setup & issue summarization | ✅ |
| 01 | Structured JSON output with Pydantic validation | ✅ |
| 02 | Reliable classification with prompt engineering | ✅ |
| 03 | Tool calling for file access | ✅ |
| 04 | Streaming UX & agent loop awareness | ✅ |
| 05 | Safety & guardrails | ✅ |
| **06** | **Production & GitHub integration** | **✅ Complete!** |

**What you've built:**
- An AI agent that reads GitHub issues
- Analyzes difficulty and extracts required concepts
- Provides mentoring advice tailored to the level
- Protected against prompt injection and path traversal
- Connected to real GitHub repos with formatted comments

---

## 🚀 Where to Go From Here

**Extend your reviewer:**
- Add a GitHub Action to run automatically on new issues
- Implement RAG for large repositories (see [Appendix: Scaling with RAG](../appendices/scaling-rag/README.md))
- Add cost tracking and token budgets
- Build a web dashboard for review analytics

**Learn more:**
- 📚 [GitHub Actions documentation](https://docs.github.com/en/actions)
- 📚 [GitHub Copilot SDK reference](https://github.com/github/copilot-sdk)
- 📚 [Building LLM applications](https://www.deeplearning.ai/courses/)

---

## 📚 Additional Resources

- 📚 [GitHub REST API documentation](https://docs.github.com/en/rest)
- 📚 [httpx documentation](https://www.python-httpx.org/)
- 📚 [Python logging best practices](https://docs.python.org/3/howto/logging.html)

---

**[← Back to Chapter 05](../05-safety-guardrails/README.md)** | **[Back to Course Home →](../README.md)**
