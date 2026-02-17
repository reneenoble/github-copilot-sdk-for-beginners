# Chapter 8 — Evaluation & Testing

![Chapter 8 banner illustration — a test harness measuring AI agent accuracy](./images/banner.png)

<!-- TODO: Add banner image to ./08-evaluation-testing/images/banner.png — An illustration (1280×640) showing a laboratory/testing setup: test tubes labeled with issue descriptions on the left, an AI agent in the middle processing them, and a results dashboard on the right showing pass/fail metrics, accuracy %, and consistency scores. Same art style as course. -->

> *"If you can't measure it, you can't improve it."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Create golden test cases with expected outputs
- ✅ Build a test harness that runs the reviewer against test data
- ✅ Measure accuracy (does the model give the right answer?)
- ✅ Measure consistency (does it give the same answer every time?)
- ✅ Validate schemas automatically
- ✅ Detect prompt drift when you change the system prompt

## Pre-requisites

- Completed [Chapter 7 — Safety & Guardrails](../07-safety-guardrails/README.md)
- All previous chapter concepts

---

## Introduction

You've built a powerful Issue Reviewer with structured output, tool calling, mentoring, and safety guardrails. But how do you know it's **working correctly**?

AI models are non-deterministic — the same input can produce different outputs on different runs. This makes testing challenging but also **critically important**. Without evaluation:

- You don't know if a prompt change improved or degraded performance
- You can't detect when the model's behavior drifts
- You can't confidently ship to production

This chapter teaches you to build an **evaluation harness** — a systematic way to test your reviewer.

---

## Key Concepts

### Golden Test Cases

A **golden test case** is an issue with a known expected output. You create these by hand based on your domain expertise:

```python
GOLDEN_TESTS = [
    {
        "name": "Typo in README",
        "issue": "Title: Fix typo\n\nThe word 'recieve' should be 'receive' in README.md.",
        "expected": {
            "difficulty_score": 1,
            "recommended_level": "Junior",
        }
    },
    {
        "name": "Security vulnerability",
        "issue": """Title: SQL injection in user search
        
        The search endpoint in src/routes/search.py passes user input directly
        to a SQL query without parameterization. This allows SQL injection.""",
        "expected": {
            "difficulty_score": 4,
            "recommended_level": "Senior",
        }
    },
    {
        "name": "Architecture migration",
        "issue": """Title: Migrate from monolith to microservices
        
        We need to decompose the monolithic application into microservices.
        This affects every module, the database, deployment, and CI/CD.""",
        "expected": {
            "difficulty_score": 5,
            "recommended_level": "Senior+",
        }
    },
]
```

> 💡 **Tip**: Start with 5–10 golden test cases covering the extremes (easiest, hardest) and the boundaries between levels.

### Accuracy Metrics

For each test case, compare the model's output with the expected output:

```python
def score_result(actual: IssueReview, expected: dict) -> dict:
    """Score a single result against expected values."""
    scores = {}

    # Exact match for difficulty score
    if "difficulty_score" in expected:
        scores["difficulty_exact"] = (
            actual.difficulty_score == expected["difficulty_score"]
        )
        scores["difficulty_close"] = (
            abs(actual.difficulty_score - expected["difficulty_score"]) <= 1
        )

    # Exact match for recommended level
    if "recommended_level" in expected:
        scores["level_match"] = (
            actual.recommended_level == expected["recommended_level"]
        )

    return scores
```

### Consistency Testing

Run the same input multiple times and check if the answer varies:

```python
async def test_consistency(client, issue: str, runs: int = 3) -> dict:
    """Run the same issue multiple times and check consistency."""
    results = []
    for i in range(runs):
        review = await run_review(client, issue)
        results.append(review)

    scores = [r.difficulty_score for r in results]
    levels = [r.recommended_level for r in results]

    return {
        "score_consistent": len(set(scores)) == 1,
        "level_consistent": len(set(levels)) == 1,
        "scores": scores,
        "levels": levels,
    }
```

![Chart showing consistency across runs — some prompts are stable, others fluctuate](./images/consistency-chart.png)

<!-- TODO: Add diagram to ./08-evaluation-testing/images/consistency-chart.png — A bar chart (800×400) showing 3 runs for each of 5 test issues. Each run is a colored bar showing the difficulty score. Consistent tests show bars of equal height; inconsistent tests show bars at different heights. Add labels: "Consistent ✅" and "Inconsistent ⚠️" under the appropriate groups. -->

### Schema Validation Testing

Ensure every response parses into your Pydantic model:

```python
def test_schema_validity(raw_content: str) -> dict:
    """Check that the response is valid JSON matching the schema."""
    try:
        review = IssueReview.model_validate_json(raw_content.strip())
        return {"valid": True, "review": review}
    except Exception as e:
        return {"valid": False, "error": str(e)}
```

### Drift Detection

When you change the system prompt, compare results against a baseline:

```python
def detect_drift(baseline: list[dict], current: list[dict]) -> list[dict]:
    """Compare current results to baseline and flag differences."""
    drifts = []
    for b, c in zip(baseline, current):
        if b["difficulty_score"] != c["difficulty_score"]:
            drifts.append({
                "test": b["name"],
                "baseline_score": b["difficulty_score"],
                "current_score": c["difficulty_score"],
                "drift": c["difficulty_score"] - b["difficulty_score"],
            })
    return drifts
```

---

## Demo Walkthrough

Here's the complete test harness. Create `test_harness.py`:

```python
import asyncio
import json
import time
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str


SYSTEM_PROMPT = """You are a GitHub issue reviewer.

Respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<specific skill>", ...],
  "mentoring_advice": "<guidance>"
}

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.
"""

# --- Golden Test Cases ---

GOLDEN_TESTS = [
    {
        "name": "Typo fix",
        "issue": "Title: Fix typo\n\nThe word 'recieve' in README.md should be 'receive'.",
        "expected_score": 1,
        "expected_level": "Junior",
    },
    {
        "name": "Simple bug fix",
        "issue": "Title: Fix off-by-one error\n\nThe loop in src/utils.py iterates one extra time, causing an IndexError.",
        "expected_score": 2,
        "expected_level": "Junior",
    },
    {
        "name": "New feature",
        "issue": "Title: Add pagination to user list\n\nThe /users endpoint returns all users. Add limit/offset pagination with proper response headers.",
        "expected_score": 3,
        "expected_level": "Mid",
    },
    {
        "name": "Security vulnerability",
        "issue": "Title: SQL injection in search\n\nThe search endpoint passes user input directly to SQL. Need parameterized queries, input validation, and audit logging.",
        "expected_score": 4,
        "expected_level": "Senior",
    },
    {
        "name": "Architecture migration",
        "issue": "Title: Migrate to microservices\n\nDecompose the monolith into microservices. Affects all modules, database, deployment, CI/CD, and requires a migration plan.",
        "expected_score": 5,
        "expected_level": "Senior+",
    },
]


async def run_review(client, issue_text: str) -> IssueReview | None:
    """Run a single review and return the parsed result."""
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
    })

    response = await session.send_and_wait({"prompt": issue_text})

    content = response.data.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]

    try:
        return IssueReview.model_validate_json(content.strip())
    except (ValidationError, json.JSONDecodeError):
        return None


async def run_accuracy_tests(client):
    """Run all golden tests and report accuracy."""
    print("📊 ACCURACY TESTS")
    print("=" * 60)

    exact_matches = 0
    close_matches = 0
    schema_valid = 0
    total = len(GOLDEN_TESTS)

    for test in GOLDEN_TESTS:
        review = await run_review(client, test["issue"])

        if review is None:
            print(f"  ❌ {test['name']}: Schema validation FAILED")
            continue

        schema_valid += 1

        score_exact = review.difficulty_score == test["expected_score"]
        score_close = abs(review.difficulty_score - test["expected_score"]) <= 1
        level_match = review.recommended_level == test["expected_level"]

        if score_exact:
            exact_matches += 1
        if score_close:
            close_matches += 1

        icon = "✅" if score_exact and level_match else "⚠️" if score_close else "❌"
        print(f"  {icon} {test['name']}: "
              f"Score {review.difficulty_score} "
              f"(expected {test['expected_score']}), "
              f"Level: {review.recommended_level} "
              f"(expected {test['expected_level']})")

    print(f"\n  Schema valid:  {schema_valid}/{total}")
    print(f"  Exact match:   {exact_matches}/{total} "
          f"({exact_matches/total*100:.0f}%)")
    print(f"  Close (±1):    {close_matches}/{total} "
          f"({close_matches/total*100:.0f}%)")
    print()


async def run_consistency_tests(client, runs: int = 3):
    """Run a subset of tests multiple times to check consistency."""
    print("🔄 CONSISTENCY TESTS")
    print("=" * 60)

    # Test with two cases at different ends
    test_cases = [GOLDEN_TESTS[0], GOLDEN_TESTS[-1]]

    for test in test_cases:
        scores = []
        levels = []

        for i in range(runs):
            review = await run_review(client, test["issue"])
            if review:
                scores.append(review.difficulty_score)
                levels.append(review.recommended_level)

        score_consistent = len(set(scores)) == 1
        level_consistent = len(set(levels)) == 1
        icon = "✅" if score_consistent and level_consistent else "⚠️"

        print(f"  {icon} {test['name']}:")
        print(f"     Scores: {scores} "
              f"({'consistent' if score_consistent else 'INCONSISTENT'})")
        print(f"     Levels: {levels} "
              f"({'consistent' if level_consistent else 'INCONSISTENT'})")

    print()


async def main():
    client = CopilotClient()
    await client.start()

    start = time.time()

    await run_accuracy_tests(client)
    await run_consistency_tests(client)

    elapsed = time.time() - start
    print(f"⏱️  Total time: {elapsed:.1f}s")

    await client.stop()


asyncio.run(main())
```

### Expected Output

```
📊 ACCURACY TESTS
============================================================
  ✅ Typo fix: Score 1 (expected 1), Level: Junior (expected Junior)
  ✅ Simple bug fix: Score 2 (expected 2), Level: Junior (expected Junior)
  ✅ New feature: Score 3 (expected 3), Level: Mid (expected Mid)
  ⚠️ Security vulnerability: Score 3 (expected 4), Level: Senior (expected Senior)
  ✅ Architecture migration: Score 5 (expected 5), Level: Senior+ (expected Senior+)

  Schema valid:  5/5
  Exact match:   4/5 (80%)
  Close (±1):    5/5 (100%)

🔄 CONSISTENCY TESTS
============================================================
  ✅ Typo fix:
     Scores: [1, 1, 1] (consistent)
     Levels: ['Junior', 'Junior', 'Junior'] (consistent)
  ✅ Architecture migration:
     Scores: [5, 5, 5] (consistent)
     Levels: ['Senior+', 'Senior+', 'Senior+'] (consistent)

⏱️  Total time: 23.4s
```

![Terminal showing test harness output with accuracy and consistency results](./images/test-harness-output.png)

<!-- TODO: Add screenshot to ./08-evaluation-testing/images/test-harness-output.png — A terminal screenshot (dark theme) showing the full test harness output: accuracy section with checkmarks/warnings, percentage scores, then consistency section with repeated run results. Show a mix of passing and near-miss results to make it realistic. -->

---

## Practice: Improving Your Test Suite

### 1. Add Boundary Test Cases

Create test issues that fall between difficulty levels:

```python
{
    "name": "Boundary: simple security fix",
    "issue": "Title: Update dependency\n\nThe bcrypt library has a known CVE. Update from v2.1 to v2.3 in requirements.txt.",
    "expected_score": 2,  # Could be 1 or 2
    "expected_level": "Junior",
}
```

### 2. Test Concept Extraction Quality

Check that extracted concepts are meaningful:

```python
def validate_concepts(review: IssueReview) -> bool:
    """Check that concepts are specific, not vague."""
    vague_terms = {"coding", "programming", "debugging", "software", "development"}
    return not any(c.lower() in vague_terms for c in review.concepts_required)
```

### 3. Build a Regression Suite

Save baseline results to a JSON file and compare against them whenever you change the prompt:

```python
def save_baseline(results: list[dict], path: str = "baseline.json"):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)

def load_baseline(path: str = "baseline.json") -> list[dict]:
    with open(path) as f:
        return json.load(f)
```

---

## Knowledge Check ✅

1. **What is a golden test case?**
   - a) A test that always passes
   - b) An issue with a known expected output for comparison
   - c) A test using the most expensive model
   - d) A test that runs only once

2. **Why is consistency testing important for AI models?**
   - a) To make the model faster
   - b) Because models are deterministic and should always match
   - c) Because models are non-deterministic and the same input may produce different outputs
   - d) To reduce API costs

3. **What does drift detection measure?**
   - a) How fast the model responds
   - b) Whether results change when the system prompt is modified
   - c) How many tokens the model uses
   - d) Whether the API is available

<details>
<summary>Answers</summary>

1. **b** — A golden test case has a known expected output that you compare against the model's actual output.
2. **c** — AI models are non-deterministic. Consistency testing reveals whether the model gives stable answers.
3. **b** — Drift detection compares current results to a baseline to find regressions caused by prompt changes.

</details>

---

## Capstone Progress 🏗️

Your Issue Reviewer now has a test harness!

| Chapter | Feature | Status |
|---------|---------|--------|
| 0 | Basic SDK setup & issue summarization | ✅ |
| 1 | Structured JSON output with Pydantic validation | ✅ |
| 2 | Reliable classification with prompt engineering | ✅ |
| 3 | Tool calling for file access | ✅ |
| 4 | Streaming UX & agent loop awareness | ✅ |
| 5 | Concept extraction & mentoring advice | ✅ |
| 6 | RAG for large repositories (optional) | ✅ |
| 7 | Safety & guardrails | ✅ |
| **8** | **Evaluation & testing** | **✅ New!** |
| 9 | Production hardening & GitHub integration | ⬜ |

## Next Step

In [Chapter 9 — Production Hardening & GitHub Integration](../09-production-hardening/README.md), you'll connect your reviewer to the GitHub API, post comments automatically, and add logging, error handling, and retries.

---

## Additional Resources

- [Evaluating LLM outputs (OpenAI guide)](https://platform.openai.com/docs/guides/evals)
- [pytest documentation](https://docs.pytest.org/)
