# Chapter 08 — Evaluation & Testing

![Chapter 8 banner illustration — a test harness measuring AI agent accuracy](./images/banner.png)

<!-- TODO: Add banner image to ./08-evaluation-testing/images/banner.png — An illustration (1280×640) showing a laboratory/testing setup: test tubes labeled with issue descriptions on the left, an AI agent in the middle processing them, and a results dashboard on the right showing pass/fail metrics, accuracy %, and consistency scores. Same art style as course. -->

> **If you can't measure it, you can't improve it. Learn to build evaluation harnesses that catch regressions before they ship.**

You've built a powerful Issue Reviewer with structured output, tool calling, mentoring, and safety guardrails. But how do you know it's **working correctly**? AI models are non-deterministic — the same input can produce different outputs on different runs. This chapter teaches you to build an **evaluation harness** — a systematic way to test your reviewer so you can confidently ship to production.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 07: Safety & Guardrails](../07-safety-guardrails/README.md)** first. You'll need your Issue Reviewer with all previous features implemented.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Create golden test cases with expected outputs
- Build a test harness that runs the reviewer against test data
- Measure accuracy (does the model give the right answer?)
- Measure consistency (does it give the same answer every time?)
- Validate schemas automatically
- Detect prompt drift when you change the system prompt

> ⏱️ **Estimated Time**: ~45 minutes (10 min reading + 35 min hands-on)

---

# Building Reliable AI Systems

## 🧩 Real-World Analogy: Quality Control on a Factory Line

<img src="./images/analogy-quality-control.png" alt="Factory quality control line comparing products against a golden sample" width="800"/>

<!-- TODO: Add analogy image to ./08-evaluation-testing/images/analogy-quality-control.png — An illustration showing a factory conveyor belt with products rolling past a QC station. A "golden sample" sits on a pedestal, and a QC inspector compares each product against it, marking some ✅ and some ❌. A dashboard shows accuracy % and consistency scores. Same art style as course. -->

Imagine a factory that makes phone cases. Every case comes off the line looking slightly different — small variations are normal. But how does the factory know whether quality is **acceptable**?

They use a **reference sample** — a "golden" case that represents perfect quality. Then they systematically test:

| QC Check | Evaluation Equivalent | What It Measures |
|---|---|---|
| Compare to the golden sample | **Golden test cases** | Is the output close to the expected answer? |
| Measure 10 cases from the same batch | **Consistency testing** | Does the same input produce similar outputs every time? |
| Check that every case has a lid, buttons, ports | **Schema validation** | Does the output have all required fields? |
| Compare this month's batch to last month | **Drift detection** | Has quality changed after a process update? |

You wouldn't ship phone cases without QC, and you shouldn't ship an AI agent without evaluation. The tricky part with AI is that *some* variation is expected (unlike factory widgets), so your tests need to allow for it — checking that scores are *close enough*, not pixel-perfect.

---

# Key Concepts

## Golden Test Cases

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

---

## Accuracy Metrics

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

---

## Consistency Testing

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

<img src="./images/consistency-chart.png" alt="Chart showing consistency across runs — some prompts are stable, others fluctuate" width="800"/>

<!-- TODO: Add diagram to ./08-evaluation-testing/images/consistency-chart.png — A bar chart (800×400) showing 3 runs for each of 5 test issues. Each run is a colored bar showing the difficulty score. Consistent tests show bars of equal height; inconsistent tests show bars at different heights. Add labels: "Consistent ✅" and "Inconsistent ⚠️" under the appropriate groups. -->

---

## Schema Validation Testing

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

---

## Drift Detection

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

# See It In Action

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

## Expected Output

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

<details>
<summary>🎬 See it in action!</summary>

![Test Harness Demo](./images/test-harness-demo.gif)

<!-- TODO: Add GIF to ./08-evaluation-testing/images/test-harness-demo.gif — A terminal recording showing: (1) python test_harness.py command, (2) accuracy test output with checkmarks, (3) consistency test output showing repeated runs. -->

*Demo output varies. Your results will differ from what's shown here.*

</details>

---

# Practice

<img src="../images/practice.png" alt="Warm desk setup ready for hands-on practice" width="800"/>

Time to put what you've learned into action.

---

## ▶️ Try It Yourself

After completing the demos above, try these experiments:

1. **Add Boundary Test Cases** — Create test issues that fall between difficulty levels:

```python
{
    "name": "Boundary: simple security fix",
    "issue": "Title: Update dependency\n\nThe bcrypt library has a known CVE. Update from v2.1 to v2.3 in requirements.txt.",
    "expected_score": 2,  # Could be 1 or 2
    "expected_level": "Junior",
}
```

2. **Test Concept Extraction Quality** — Check that extracted concepts are meaningful:

```python
def validate_concepts(review: IssueReview) -> bool:
    """Check that concepts are specific, not vague."""
    vague_terms = {"coding", "programming", "debugging", "software", "development"}
    return not any(c.lower() in vague_terms for c in review.concepts_required)
```

3. **Build a Regression Suite** — Save baseline results to a JSON file and compare against them whenever you change the prompt:

```python
def save_baseline(results: list[dict], path: str = "baseline.json"):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)

def load_baseline(path: str = "baseline.json") -> list[dict]:
    with open(path) as f:
        return json.load(f)
```

---

## 📝 Assignment

### Main Challenge: Build Your Complete Evaluation Suite

Extend the test harness from this chapter to create a production-ready evaluation suite:

1. Add at least 3 more golden test cases covering edge cases
2. Implement concept validation that flags vague terms
3. Create a baseline file and implement drift detection
4. Run your full suite and document the accuracy percentages

**Success criteria**: Your test suite runs end-to-end and produces a clear report showing accuracy, consistency, and any drift from baseline.

<details>
<summary>💡 Hints</summary>

**Good boundary test cases:**
- An issue that's borderline Junior/Mid (simple feature addition)
- An issue that's borderline Senior/Senior+ (complex but contained)
- An issue with ambiguous scope

**Common issues:**
- Forgetting to handle `None` results from failed parsing
- Not accounting for natural model variance (use ±1 tolerance)
- Running too few consistency tests (3 is minimum, 5 is better)

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Too few golden tests | Can't detect regressions | Start with 5-10 covering extremes |
| Expecting exact matches | Too many false failures | Use ±1 tolerance for scores |
| Not running consistency tests | Miss flaky behavior | Run each test 3+ times |
| Manual baseline management | Baselines get stale | Automate baseline save/load |

### Troubleshooting

**"All my consistency tests fail"** — The model may be too variable. Try lowering temperature or making your rubric more explicit.

**"Accuracy is great but consistency is poor"** — Your rubric may have ambiguous boundaries. Add clearer criteria for edge cases.

**"Results changed after I modified the prompt"** — That's drift detection working! Compare against baseline to see if the change is an improvement or regression.

---

### 🧠 Knowledge Check

<details>
<summary>1. What is a golden test case?</summary>

**b) An issue with a known expected output for comparison** — A golden test case has a known expected output that you compare against the model's actual output.

</details>

<details>
<summary>2. Why is consistency testing important for AI models?</summary>

**c) Because models are non-deterministic and the same input may produce different outputs** — AI models are non-deterministic. Consistency testing reveals whether the model gives stable answers.

</details>

<details>
<summary>3. What does drift detection measure?</summary>

**b) Whether results change when the system prompt is modified** — Drift detection compares current results to a baseline to find regressions caused by prompt changes.

</details>

</details>

---

# Summary

## 🔑 Key Takeaways

1. **Golden test cases are your ground truth** — create hand-labeled examples covering the extremes and boundaries of your classification
2. **Accuracy measures correctness** — compare model output against expected values, allowing for reasonable tolerance
3. **Consistency measures stability** — run the same input multiple times to detect flaky behavior
4. **Drift detection catches regressions** — save baselines and compare after every prompt change
5. **Schema validation is table stakes** — every response should parse into your Pydantic model

> 📚 **Glossary**: New to terms like "golden test" or "drift detection"? See the [Glossary](../GLOSSARY.md) for definitions.

---

## 🏗️ Capstone Progress

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

## ➡️ What's Next

You've built a comprehensive evaluation harness. In **[Chapter 09: Production Hardening & GitHub Integration](../09-production-hardening/README.md)**, you'll learn:

- How to connect your reviewer to the GitHub API
- Post comments on issues automatically
- Add logging, error handling, and retries
- Deploy your Issue Reviewer to production

---

## 📚 Additional Resources

- 📚 [Evaluating LLM outputs (OpenAI guide)](https://platform.openai.com/docs/guides/evals)
- 📚 [pytest documentation](https://docs.pytest.org/)

---

**[← Back to Chapter 07](../07-safety-guardrails/README.md)** | **[Continue to Chapter 09 →](../09-production-hardening/README.md)**
