"""
Chapter 06 — Shipping to Production: Solution
GitHub Copilot SDK for Beginners

Production-ready Issue Reviewer that reads real issues from the GitHub API,
posts structured review comments, and includes logging and retry logic.
"""

import asyncio
import json
import logging
import os
import httpx
from copilot import CopilotClient, define_tool
from copilot.session import PermissionHandler
from copilot.generated.session_events import AssistantMessageData
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


# --- Configuration ---

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


# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("issue-reviewer")


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


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def with_retry(func, *args, max_retries: int = 3, delay: float = 1.0):
    """Run an async function with exponential backoff retries."""
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except httpx.HTTPStatusError as e:
            # Don't retry permanent errors
            if e.response.status_code in (401, 403, 404):
                raise
            if attempt == max_retries - 1:
                raise
            wait = delay * (2 ** attempt)
            logger.warning("Attempt %d failed: %s. Retrying in %.1fs...",
                           attempt + 1, e, wait)
            await asyncio.sleep(wait)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = delay * (2 ** attempt)
            logger.warning("Attempt %d failed: %s. Retrying in %.1fs...",
                           attempt + 1, e, wait)
            await asyncio.sleep(wait)


async def _fetch_issue(owner: str, repo: str, issue_number: int) -> dict:
    async with httpx.AsyncClient() as client:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
        response = await client.get(url, headers=_headers())
        response.raise_for_status()
        return response.json()


async def fetch_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Fetch an issue from the GitHub API with retry."""
    logger.info("Fetching issue #%d from %s/%s", issue_number, owner, repo)
    return await with_retry(_fetch_issue, owner, repo, issue_number)


async def _post_comment(owner: str, repo: str, issue_number: int, body: str):
    async with httpx.AsyncClient() as client:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = await client.post(url, headers=_headers(), json={"body": body})
        response.raise_for_status()
        return response.json()


async def post_comment(owner: str, repo: str, issue_number: int, body: str):
    """Post a comment on a GitHub issue with retry."""
    logger.info("Posting review comment on issue #%d", issue_number)
    return await with_retry(_post_comment, owner, repo, issue_number, body)


# --- Tool ---

ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml",
                      ".yml", ".toml", ".cfg", ".ini"}


class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    repo_root = os.path.realpath(Config.REPO_PATH)
    full_path = os.path.realpath(os.path.join(repo_root, params.file_path))

    if not full_path.startswith(repo_root):
        return "Error: Access denied — path is outside the repository"

    ext = os.path.splitext(full_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"Error: File type '{ext}' is not allowed"

    try:
        with open(full_path, "r") as f:
            content = f.read()
            return content[:10_000] if len(content) > 10_000 else content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


# --- System Prompt ---

SYSTEM_PROMPT = """You are a GitHub issue reviewer. Analyze GitHub issues and
produce structured reviews. Respond ONLY with a JSON object matching this schema:

{
  "summary": "<one-sentence summary>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<skill>", ...],
  "mentoring_advice": "<actionable advice>",
  "files_analyzed": ["<file path>", ...]
}

Difficulty rubric:
1 — Junior: Docs, typos, config changes. No logic.
2 — Junior/Mid: Simple bug, single file, clear fix.
3 — Mid: Feature in one subsystem, 2-5 files.
4 — Senior: Cross-cutting concern (perf, security). Multiple systems.
5 — Senior+: Architecture, migrations, breaking changes.
"""


# --- Markdown Formatter ---

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


# --- Reviewer ---

async def run_review(copilot_client: CopilotClient, issue_text: str) -> IssueReview | None:
    """Run the issue reviewer and return a structured review."""
    session = await copilot_client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model=Config.MODEL,
        system_message={"mode": "replace", "content": SYSTEM_PROMPT},
        tools=[get_file_contents],
    )

    response = await session.send_and_wait(issue_text)

    if not response or not isinstance(response.data, AssistantMessageData):
        logger.error("No response received from model")
        return None

    try:
        review = IssueReview.model_validate_json(response.data.content)
        logger.info("Review complete: score=%d, level=%s",
                    review.difficulty_score, review.recommended_level)
        return review
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error("Failed to parse model response: %s", e)
        logger.debug("Raw response: %s", response.data.content)
        return None


# --- Test Harness ---

GOLDEN_TESTS = [
    {
        "name": "Typo fix",
        "issue": "Title: Fix typo\n\nChange 'recieve' to 'receive' in README.md.",
        "expected_score": 1,
        "expected_level": "Junior",
    },
    {
        "name": "Security vulnerability",
        "issue": (
            "Title: SQL injection in search\n\n"
            "The search endpoint passes user input directly to SQL without parameterization."
        ),
        "expected_score": 4,
        "expected_level": "Senior",
    },
]


async def run_tests(copilot_client: CopilotClient):
    """Run golden tests and report results."""
    logger.info("Running %d golden tests...", len(GOLDEN_TESTS))
    passed = 0

    for test in GOLDEN_TESTS:
        review = await run_review(copilot_client, test["issue"])
        if review is None:
            print(f"❌ {test['name']}: no response")
            continue

        score_ok = abs(review.difficulty_score - test["expected_score"]) <= 1
        level_ok = review.recommended_level == test["expected_level"]

        if score_ok and level_ok:
            print(f"✅ {test['name']}")
            passed += 1
        else:
            print(f"❌ {test['name']}: got {review.difficulty_score}/{review.recommended_level}")

    print(f"\n{passed}/{len(GOLDEN_TESTS)} tests passed")


# --- Main ---

async def main():
    Config.validate()

    copilot_client = CopilotClient()
    await copilot_client.start()

    issue_number = int(os.environ.get("ISSUE_NUMBER", "0"))

    if issue_number:
        # Production mode: review a real issue
        issue = await fetch_issue(Config.GITHUB_OWNER, Config.GITHUB_REPO, issue_number)
        issue_text = f"Title: {issue['title']}\n\n{issue['body'] or ''}"

        review = await run_review(copilot_client, issue_text)

        if review:
            comment = format_review_comment(review)
            print(comment)

            if os.environ.get("POST_COMMENT", "").lower() == "true":
                await post_comment(Config.GITHUB_OWNER, Config.GITHUB_REPO,
                                   issue_number, comment)
                logger.info("Comment posted successfully")
    else:
        # Test mode: run golden tests
        await run_tests(copilot_client)

    await copilot_client.stop()


asyncio.run(main())
