# Chapter 1 — Structured Output: Stop Parsing Strings

![Chapter 1 banner illustration — structured data emerging from messy text](./images/banner.png)

<!-- TODO: Add banner image to ./01-structured-output/images/banner.png — An illustration (1280×640) showing messy, unstructured text on the left transforming into clean, organized JSON blocks on the right, with a magical/AI glow in between. Same art style as repo banner. -->

> *"If you're parsing AI output with regex, you're doing it wrong."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Explain why structured output matters for reliable AI applications
- ✅ Use system prompts to request JSON responses from the model
- ✅ Define Pydantic models to validate model output
- ✅ Handle validation errors gracefully

## Pre-requisites

- Completed [Chapter 0 — Getting Started](../00-getting-started/README.md)
- `github-copilot-sdk` and `pydantic` installed

---

## Introduction

In Chapter 0, you asked the model to summarize an issue and got back free-form text. That works great for humans reading the output — but what if you want to use the data programmatically?

Imagine you want to build a dashboard that shows issue difficulty scores, or an automation that applies labels based on the analysis. You need **structured, predictable, machine-readable output** — not paragraphs of prose.

This is where **structured output** comes in. Instead of hoping the model returns data in the right format, you **constrain** it to produce exactly the shape you need.

## Key Concepts

### Why Structured Output Matters

When you ask a model for free-form text, you get responses that vary in format every time:

```
"This is a medium-difficulty issue, probably a 3 out of 5..."
"Difficulty: Medium (3/5)"
"I'd rate this as moderately difficult."
```

All say roughly the same thing, but parsing any of these programmatically is fragile. **Structured output** solves this by having the model return a consistent JSON object:

```json
{
  "summary": "Login crash on mobile Safari due to premature autofocus",
  "difficulty_score": 3,
  "recommended_level": "Mid"
}
```

![Comparison diagram showing free-text vs. structured output side by side](./images/freetext-vs-structured.png)

<!-- TODO: Add diagram to ./01-structured-output/images/freetext-vs-structured.png — A side-by-side comparison: left side shows 3 different free-text responses (messy, inconsistent), right side shows 3 identical JSON objects (clean, consistent). Title: "Free Text vs. Structured Output". -->

### How to Get Structured Output

With the Copilot SDK, you get structured output by being explicit in your **system message**. You tell the model exactly what JSON shape to return and instruct it to respond only with JSON.

### Validating with Pydantic

[Pydantic](https://docs.pydantic.dev/) is a Python library for data validation. You define a model class with typed fields, and Pydantic validates that incoming data matches your schema.

```python
from pydantic import BaseModel, Field

class IssueAnalysis(BaseModel):
    summary: str = Field(description="One-sentence summary of the issue")
    difficulty_score: int = Field(ge=1, le=5, description="Difficulty from 1-5")
    recommended_level: str = Field(description="Junior, Mid, Senior, or Senior+")
```

When the model returns JSON, you parse it with Pydantic:

```python
import json

# Parse the model's response as JSON, then validate with Pydantic
data = json.loads(response.data.content)
analysis = IssueAnalysis(**data)
print(analysis.difficulty_score)  # Guaranteed to be an int between 1-5
```

> ⚠️ **Warning:** The model might occasionally return invalid JSON or miss fields. Always wrap parsing in a try/except block.

---

## Demo / Code Walkthrough

### The Problem: Loose Text Responses

First, let's see what happens with a free-form response:

```python
import asyncio
from copilot import CopilotClient

SAMPLE_ISSUE = """
Title: Database connection pool exhaustion under load

Our PostgreSQL connection pool runs out of connections during peak hours.
The app uses SQLAlchemy with a pool size of 10. Under load testing with
100 concurrent users, we see "QueuePool limit exceeded" errors after
about 2 minutes. Need to implement connection pooling with PgBouncer
or increase pool size with proper timeout handling.
"""

async def main():
    client = CopilotClient()
    await client.start()
    session = await client.create_session({"model": "gpt-4.1"})

    response = await session.send_and_wait({
        "prompt": f"Analyze this GitHub issue and tell me the difficulty level:\n\n{SAMPLE_ISSUE}"
    })

    print("Free-form response:")
    print(response.data.content)
    # Output varies! Could be a paragraph, a list, a number... unpredictable.

    await session.destroy()
    await client.stop()

asyncio.run(main())
```

Every time you run this, the format changes. Not great for automation.

### The Solution: Structured JSON Response

Now, let's constrain the output with a system message and Pydantic validation:

```python
import asyncio
import json
from copilot import CopilotClient
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    """Schema for structured issue analysis output."""
    summary: str = Field(description="One-sentence summary of the issue")
    difficulty_score: int = Field(
        ge=1, le=5,
        description="Difficulty from 1 (trivial) to 5 (expert-level)"
    )
    recommended_level: str = Field(
        description="One of: Junior, Mid, Senior, Senior+"
    )


SYSTEM_PROMPT = """You are a GitHub issue analyzer. When given an issue, respond
with ONLY a JSON object (no markdown, no code fences, no extra text) matching
this exact schema:

{
  "summary": "One-sentence summary of the issue",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+"
}

Rules:
- difficulty_score must be an integer from 1 to 5
- recommended_level must be exactly one of: Junior, Mid, Senior, Senior+
- summary must be a single sentence
- Return ONLY the JSON object, nothing else
"""

SAMPLE_ISSUE = """
Title: Database connection pool exhaustion under load

Our PostgreSQL connection pool runs out of connections during peak hours.
The app uses SQLAlchemy with a pool size of 10. Under load testing with
100 concurrent users, we see "QueuePool limit exceeded" errors after
about 2 minutes. Need to implement connection pooling with PgBouncer
or increase pool size with proper timeout handling.
"""


async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT,
        }
    })

    response = await session.send_and_wait({
        "prompt": f"Analyze this GitHub issue:\n\n{SAMPLE_ISSUE}"
    })

    # Parse and validate the response
    try:
        raw = response.data.content
        data = json.loads(raw)
        analysis = IssueAnalysis(**data)

        print(f"Summary:     {analysis.summary}")
        print(f"Difficulty:  {analysis.difficulty_score}/5")
        print(f"Level:       {analysis.recommended_level}")
    except json.JSONDecodeError:
        print("Error: Model did not return valid JSON")
        print(f"Raw response: {response.data.content}")
    except Exception as e:
        print(f"Validation error: {e}")

    await session.destroy()
    await client.stop()


asyncio.run(main())
```

![Screenshot showing the structured output in the terminal with labeled fields](./images/structured-output-terminal.png)

<!-- TODO: Add screenshot to ./01-structured-output/images/structured-output-terminal.png — Terminal output showing clean, formatted results: "Summary: Database connection pool...", "Difficulty: 4/5", "Level: Senior". Should look professional and readable. -->

Now the output is **consistent, predictable, and validated**. Every run produces the same shape of data.

---

## 🧠 Knowledge Check

1. Why is structured output better than free-text for automation?
   - A) It's faster
   - B) It produces consistent, parseable data that code can reliably use ✅
   - C) It uses fewer tokens

2. What happens if the model returns a `difficulty_score` of 7 with the Pydantic model above?
   - A) It silently truncates to 5
   - B) Pydantic raises a validation error ✅
   - C) It works fine

3. Why do we use `"mode": "replace"` in the system message?
   - A) To add our instructions after the default system prompt
   - B) To fully replace the system prompt so we control the output format ✅
   - C) To disable the model's safety features

---

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| 00 | Basic issue summary | ✅ |
| **01** | **Structured output** | **🔲 ← You are here** |
| 02 | Reliable classification | 🔲 |
| 03 | Tool calling (file fetch) | 🔲 |
| 04 | Streaming UX | 🔲 |
| 05 | Concepts & mentoring | 🔲 |
| 06 | RAG for large repos | 🔲 |
| 07 | Safety & guardrails | 🔲 |
| 08 | Evaluation & testing | 🔲 |
| 09 | Production hardening | 🔲 |

**Your task:** Extend the Issue Reviewer to return structured output with a summary, difficulty score, and recommended level.

See [assignment.md](./assignment.md) for full instructions.

---

## Additional Resources

- 📖 [Pydantic Documentation](https://docs.pydantic.dev/)
- 📖 [GitHub Copilot SDK — System Message Customization](https://github.com/github/copilot-sdk/blob/main/python/README.md#system-message-customization)
- 📚 [JSON Schema Specification](https://json-schema.org/)

---

## Next Steps

Your output is now structured — but is it *consistent*? In the next lesson, you'll learn **prompt engineering techniques** to make the classification reliable across multiple runs. → [Chapter 2 — Prompt Engineering](../02-prompt-engineering/README.md)
