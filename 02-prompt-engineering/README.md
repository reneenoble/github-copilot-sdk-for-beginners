# Chapter 2 — Prompt Engineering for Reliable Classification

![Chapter 2 banner illustration — a tuning dial being adjusted for precision](./images/banner.png)

<!-- TODO: Add banner image to ./02-prompt-engineering/images/banner.png — An illustration (1280×640) showing a precision tuning dial or mixing board with labels like "Temperature", "Rubric", "Few-shot" being carefully adjusted by a developer. Same art style as course. -->

> *"A good prompt doesn't just ask the right question — it defines what a right answer looks like."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Write clear system instructions with rubrics
- ✅ Use few-shot examples to guide model behavior
- ✅ Understand how temperature affects output consistency
- ✅ Constrain the model to allowed values only

## Pre-requisites

- Completed [Chapter 1 — Structured Output](../01-structured-output/README.md)
- Familiarity with your `IssueAnalysis` Pydantic model

---

## Introduction

In Chapter 1, you got the model to return structured JSON. But if you run the same issue through your analyzer multiple times, you might get different difficulty scores each time — a 3 on one run, a 4 on the next.

For an automated system, this inconsistency is a problem. If your bot labels an issue as "Senior" one minute and "Mid" the next, nobody will trust it.

This chapter teaches you how to make your classification **reliable and repeatable** through prompt engineering techniques.

## Key Concepts

### System Instructions: The Rules of Engagement

The **system message** sets the model's persona, rules, and constraints. A vague system prompt produces vague results. A specific, rubric-based system prompt produces consistent results.

**Bad system prompt:**
```
Analyze GitHub issues and rate their difficulty.
```

**Good system prompt:**
```
You are a GitHub issue difficulty classifier. Rate each issue using this rubric:

Score 1 (Junior): Typos, copy changes, config tweaks. No logic changes.
Score 2 (Junior-Mid): Simple bug fixes with clear error messages. Single file change.
Score 3 (Mid): Feature work requiring understanding of one subsystem. 2-5 files.
Score 4 (Senior): Cross-cutting concerns, performance, security. Multiple subsystems.
Score 5 (Senior+): Architecture changes, data migrations, backward compatibility.
```

![Side-by-side comparison of vague vs. specific system prompts and their outputs](./images/vague-vs-specific-prompt.png)

<!-- TODO: Add diagram to ./02-prompt-engineering/images/vague-vs-specific-prompt.png — Two-column comparison: Left shows a vague prompt with 3 inconsistent outputs (scores 2, 4, 3). Right shows a rubric-based prompt with 3 consistent outputs (all score 4). Title: "Vague vs. Specific System Prompts". -->

### Few-Shot Examples

**Few-shot prompting** means including examples of correct input/output pairs in your system prompt. The model mimics the pattern you demonstrate.

```
Example 1:
Issue: "Fix typo in README — 'recieve' should be 'receive'"
Output: {"summary": "Fix typo in README", "difficulty_score": 1, "recommended_level": "Junior"}

Example 2:
Issue: "Add rate limiting to the API. Need to track requests per user per hour and return 429 when exceeded. Must work across multiple server instances using Redis."
Output: {"summary": "Implement distributed rate limiting with Redis", "difficulty_score": 4, "recommended_level": "Senior"}
```

> 💡 **Tip:** Include 2–3 few-shot examples covering the range of difficulty levels (easy, medium, hard) for the best results.

### Constraining Allowed Values

Explicitly list the allowed values in your prompt and state that only those values are acceptable:

```
recommended_level must be EXACTLY one of these values: "Junior", "Mid", "Senior", "Senior+"
Do NOT use any other values. Do NOT use "Intermediate", "Beginner", "Expert", etc.
```

### Temperature and Determinism

**Temperature** controls randomness in the model's output:
- **Low temperature (0.0–0.3):** More deterministic, consistent outputs
- **High temperature (0.7–1.0):** More creative, varied outputs

For classification tasks, you want **low temperature** for consistency.

> 📝 **Note:** The Copilot SDK doesn't expose temperature directly in the session config as it's managed by the underlying model configuration. However, you can influence determinism through clear, constrained prompts with rubrics and few-shot examples. The system prompt is your primary tool for consistency.

---

## Demo / Code Walkthrough

### Comparing Unstable vs. Stable Classification

Let's see the difference between a vague prompt and a rubric-based prompt by running the same issue 3 times with each.

```python
import asyncio
import json
from copilot import CopilotClient
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: str


VAGUE_PROMPT = """Analyze GitHub issues and return JSON with summary,
difficulty_score (1-5), and recommended_level."""


RUBRIC_PROMPT = """You are a GitHub issue difficulty classifier. You MUST respond
with ONLY a valid JSON object (no markdown, no code fences).

## Difficulty Rubric

Score 1 — Junior: Typos, documentation, config changes. No logic changes needed.
Score 2 — Junior/Mid: Simple bug fix with clear error. Single file, <20 lines changed.
Score 3 — Mid: Feature work in one subsystem. Requires understanding of 2-5 files.
Score 4 — Senior: Cross-cutting concerns (perf, security, APIs). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, data migration, backward compatibility.

## Required Output Format

{
  "summary": "<one sentence>",
  "difficulty_score": <1-5 integer based on rubric above>,
  "recommended_level": "<EXACTLY one of: Junior, Mid, Senior, Senior+>"
}

## Rules
- Apply the rubric strictly — match the issue to the closest score description
- recommended_level mapping: 1→Junior, 2→Junior, 3→Mid, 4→Senior, 5→Senior+
- Return ONLY the JSON object

## Examples

Issue: "Fix typo: 'recieve' → 'receive' in login form label"
{"summary": "Fix typo in login form label", "difficulty_score": 1, "recommended_level": "Junior"}

Issue: "Implement distributed rate limiting with Redis across multiple server instances"
{"summary": "Add Redis-based distributed rate limiting", "difficulty_score": 4, "recommended_level": "Senior"}
"""


TEST_ISSUE = """
Title: Add pagination to the /api/users endpoint

The /api/users endpoint currently returns all users in a single response.
With 50,000+ users in production, this causes timeouts and excessive memory
usage. Need to add cursor-based pagination with configurable page size.
Should also update the API documentation and add pagination to the
frontend user list component.
"""


async def main():
    client = CopilotClient()
    await client.start()

    # Run 3 times with the vague prompt
    print("=== VAGUE PROMPT (3 runs) ===")
    for i in range(3):
        session = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {"mode": "replace", "content": VAGUE_PROMPT},
        })
        response = await session.send_and_wait({
            "prompt": f"Analyze:\n\n{TEST_ISSUE}"
        })
        try:
            data = json.loads(response.data.content)
            analysis = IssueAnalysis(**data)
            print(f"  Run {i+1}: score={analysis.difficulty_score}, level={analysis.recommended_level}")
        except Exception as e:
            print(f"  Run {i+1}: Parse error — {e}")
        await session.destroy()

    # Run 3 times with the rubric prompt
    print("\n=== RUBRIC PROMPT (3 runs) ===")
    for i in range(3):
        session = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {"mode": "replace", "content": RUBRIC_PROMPT},
        })
        response = await session.send_and_wait({
            "prompt": f"Analyze:\n\n{TEST_ISSUE}"
        })
        try:
            data = json.loads(response.data.content)
            analysis = IssueAnalysis(**data)
            print(f"  Run {i+1}: score={analysis.difficulty_score}, level={analysis.recommended_level}")
        except Exception as e:
            print(f"  Run {i+1}: Parse error — {e}")
        await session.destroy()

    await client.stop()


asyncio.run(main())
```

![Terminal output showing inconsistent scores with vague prompt vs. consistent scores with rubric](./images/consistency-comparison.png)

<!-- TODO: Add screenshot to ./02-prompt-engineering/images/consistency-comparison.png — Terminal output showing: "VAGUE PROMPT" with scores varying (3, 4, 3) and levels varying (Mid, Senior, Mid), then "RUBRIC PROMPT" with consistent scores (3, 3, 3) and levels (Mid, Mid, Mid). -->

---

## 🧠 Knowledge Check

1. What is the main benefit of including a rubric in your system prompt?
   - A) It makes the model respond faster
   - B) It provides clear criteria so the model classifies consistently ✅
   - C) It reduces token usage

2. How many few-shot examples should you typically include?
   - A) 0 — examples are wasteful
   - B) 2–3 covering the range of expected outputs ✅
   - C) 10+ for maximum accuracy

3. For a classification task, should you use high or low temperature?
   - A) High — more creative outputs are better
   - B) Low — more consistent, deterministic outputs ✅
   - C) It doesn't matter

---

## 📖 Extra Reading: Model Selection & Configuration

Different models offer different tradeoffs:

| Model | Best For | Tradeoff |
|-------|----------|----------|
| `gpt-4.1` | General-purpose, good reasoning | Balanced speed/quality |
| `gpt-5` | Complex reasoning tasks | Slower, more expensive |
| `claude-sonnet-4.5` | Nuanced analysis, long context | Different reasoning style |

Use `await client.list_models()` to see available models. For classification tasks where consistency matters more than creativity, faster models with clear rubrics often outperform slower models with vague prompts.

---

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| 00 | Basic issue summary | ✅ |
| 01 | Structured output | ✅ |
| **02** | **Reliable classification** | **🔲 ← You are here** |
| 03 | Tool calling (file fetch) | 🔲 |
| 04 | Streaming UX | 🔲 |
| 05 | Concepts & mentoring | 🔲 |
| 06 | RAG for large repos | 🔲 |
| 07 | Safety & guardrails | 🔲 |
| 08 | Evaluation & testing | 🔲 |
| 09 | Production hardening | 🔲 |

**Your task:** Add a rubric and few-shot examples to your Issue Reviewer for consistent classification.

See [assignment.md](./assignment.md) for full instructions.

---

## Additional Resources

- 📖 [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- 📖 [Copilot SDK — System Message Customization](https://github.com/github/copilot-sdk/blob/main/python/README.md#system-message-customization)

---

## Next Steps

Your agent now classifies issues consistently — but it can only read what you paste into the prompt. In the next chapter, you'll give it **tools** to fetch repository files on its own. → [Chapter 3 — Tool Calling](../03-tool-calling/README.md)
