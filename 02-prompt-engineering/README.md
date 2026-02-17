# Chapter 02 — Prompt Engineering for Reliable Classification

![Chapter 2 banner illustration — a tuning dial being adjusted for precision](./images/banner.png)

<!-- TODO: Add banner image to ./02-prompt-engineering/images/banner.png — An illustration (1280×640) showing a precision tuning dial or mixing board with labels like "Temperature", "Rubric", "Few-shot" being carefully adjusted by a developer. Same art style as course. -->

> **A good prompt doesn't just ask the right question — it defines what a right answer looks like. Learn to make your classification reliable and repeatable.**

In Chapter 01, you got structured JSON output. But run the same issue through your analyzer multiple times — you might get a score of 3 one time and 4 the next. For an automated system, that inconsistency is a deal-breaker. This chapter teaches you how to make classification **reliable** through prompt engineering.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 01: Structured Output](../01-structured-output/README.md)** first. You'll need your `IssueAnalysis` Pydantic model.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Write clear system instructions with rubrics
- Use few-shot examples to guide model behavior
- Understand how temperature affects output consistency
- Constrain the model to allowed values only

> ⏱️ **Estimated Time**: ~40 minutes (15 min reading + 25 min hands-on)

---

# Making Classification Reliable

## 🧩 Real-World Analogy: Training a New Employee

<img src="./images/analogy-training-employee.png" alt="Training a new employee with rubric and examples" width="800"/>

<!-- TODO: Add analogy image to ./02-prompt-engineering/images/analogy-training-employee.png — An illustration showing a manager at a whiteboard with a rubric chart, handing a stack of example essays to a new employee at a desk. The employee's thought bubble shows organized criteria. Same art style as course. -->

Imagine you've just hired someone to grade student essays. On day one, you say: *"Read each essay and give it a grade."*

They come back with wildly inconsistent results — an A for a mediocre essay, a C for a great one. Not because they're incompetent, but because you never told them **what a good essay looks like**.

Now imagine instead you give them:

| What You Provide | Prompt Engineering Term | What It Does |
|---|---|---|
| A scoring rubric | **System prompt with rubric** | Defines what each grade means |
| Three graded example essays | **Few-shot examples** | Shows the expected standard |
| "Only use grades A through F" | **Constrained values** | Prevents invented grades like "A++++" |
| "If unsure, grade conservatively" | **Tiebreaker rules** | Handles edge cases consistently |

With clear instructions and examples, the new hire produces grades you can trust. That's exactly what prompt engineering does for an AI model — same capability, dramatically better results through better instructions.

---

# Key Concepts

Let's understand the prompt engineering techniques that make classification reliable.

---

## System Instructions: The Rules of Engagement

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

---

## Few-Shot Examples

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

---

## Constraining Allowed Values

Explicitly list the allowed values in your prompt and state that only those values are acceptable:

```
recommended_level must be EXACTLY one of these values: "Junior", "Mid", "Senior", "Senior+"
Do NOT use any other values. Do NOT use "Intermediate", "Beginner", "Expert", etc.
```

---

## Temperature and Determinism

**Temperature** controls randomness in the model's output:
- **Low temperature (0.0–0.3):** More deterministic, consistent outputs
- **High temperature (0.7–1.0):** More creative, varied outputs

For classification tasks, you want **low temperature** for consistency.

> 📝 **Note:** The Copilot SDK doesn't expose temperature directly in the session config as it's managed by the underlying model configuration. However, you can influence determinism through clear, constrained prompts with rubrics and few-shot examples. The system prompt is your primary tool for consistency.

---

# See It In Action

Let's compare a vague prompt with a rubric-based prompt by running the same issue 3 times with each.

> 💡 **About Example Outputs**: The sample outputs shown throughout this course are illustrative. Because AI responses vary each time, your results will differ in wording, formatting, and detail.

## Comparing Unstable vs. Stable Classification

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

<details>
<summary>🎬 See it in action!</summary>

![Consistency Comparison Demo](./images/consistency-demo.gif)

<!-- TODO: Add GIF to ./02-prompt-engineering/images/consistency-demo.gif — A terminal recording showing the vague prompt runs with varying scores, then rubric prompt runs with consistent scores. -->

*Demo output varies. Your results will differ from what's shown here.*

</details>

**The takeaway**: A clear rubric + few-shot examples dramatically improves consistency.

---

## 📖 Extra Reading: Model Selection & Configuration

<details>
<summary>Click to expand model comparison</summary>

Different models offer different tradeoffs:

| Model | Best For | Tradeoff |
|-------|----------|----------|
| `gpt-4.1` | General-purpose, good reasoning | Balanced speed/quality |
| `gpt-5` | Complex reasoning tasks | Slower, more expensive |
| `claude-sonnet-4.5` | Nuanced analysis, long context | Different reasoning style |

Use `await client.list_models()` to see available models. For classification tasks where consistency matters more than creativity, faster models with clear rubrics often outperform slower models with vague prompts.

</details>

---

# Practice

<img src="../images/practice.png" alt="Warm desk setup ready for hands-on practice" width="800"/>

Time to put what you've learned into action.

---

## ▶️ Try It Yourself

After completing the demo above, try these experiments:

1. **Adjust temperature mentally** — Make your prompt more explicit and observe if consistency improves

2. **Improve a vague system prompt** — Take the `VAGUE_PROMPT` and add a rubric. Run it 3 times.

3. **Add reasoning requirements** — Before the classification, ask the model to explain its reasoning, then give the score

4. **Test boundary cases** — Create an issue that's ambiguous (between 2 and 3). See if the rubric helps.

---

## 📝 Assignment

### Main Challenge: Add Reliable Classification to Your Issue Reviewer

Upgrade your Issue Reviewer with prompt engineering techniques:

1. Add a **detailed rubric** with clear criteria for each difficulty score (1-5)

2. Add **2-3 few-shot examples** covering easy, medium, and hard issues

3. Add **explicit value constraints** — list exactly which values are allowed for `recommended_level`

4. Test by running the **same issue 3 times** — scores should be consistent

**Success criteria**: Running your reviewer on the same issue 3 times produces identical scores.

See [assignment.md](./assignment.md) for full instructions.

<details>
<summary>💡 Hints</summary>

**Rubric structure:**
```
Score 1 — Junior: [specific criteria]
Score 2 — Junior/Mid: [specific criteria]
...
```

**Few-shot format:**
```
Issue: "Fix typo in README"
{"summary": "...", "difficulty_score": 1, ...}
```

**Common issues:**
- Rubric too vague — use specific criteria like "single file" or "multiple subsystems"
- Missing tiebreaker rules — add "If unsure between two scores, choose the lower one"
- Examples too similar — cover the full range of difficulty levels

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Rubric too vague | Model interprets criteria differently each time | Use specific, measurable criteria |
| No few-shot examples | Model invents its own interpretation | Add 2-3 examples covering the range |
| Examples all same difficulty | Model calibrates poorly | Include easy, medium, and hard examples |
| No tiebreaker rules | Model wavers on edge cases | Add "If unsure, choose the lower score" |

### Troubleshooting

**Scores still vary** — Your rubric may have overlapping criteria. Make boundaries clearer (e.g., "1-2 files" vs "3-5 files").

**Model uses wrong values** — Be more explicit: "ONLY use these exact values: Junior, Mid, Senior, Senior+"

**Model ignores rubric** — Move the rubric higher in the prompt. Models pay more attention to early content.

</details>

---

# Summary

## 🔑 Key Takeaways

1. **Vague prompts produce vague results** — a rubric with clear criteria is essential
2. **Few-shot examples calibrate the model** — show it what good output looks like
3. **Explicit constraints prevent drift** — list exact allowed values
4. **Test for consistency** — run the same input multiple times to verify reliability

> 📚 **Glossary**: New to terms like "few-shot" or "temperature"? See the [Glossary](../GLOSSARY.md) for definitions.

---

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| 00 | Basic issue summary | ✅ |
| 01 | Structured output with rich fields | ✅ |
| **02** | **Reliable classification** | **🔲 ← You are here** |
| 03 | Tool calling (file fetch) | 🔲 |
| 04 | Streaming UX | 🔲 |
| 05 | Safety & guardrails | 🔲 |
| 06 | Production & GitHub integration | 🔲 |

---

## ➡️ What's Next

Your agent now classifies issues consistently — but it can only read what you paste into the prompt. Real issues often reference files: "The bug is in `src/auth/login.py`..."

In **[Chapter 03: Tool Calling](../03-tool-calling/README.md)**, you'll learn:

- How to define custom tools with `@define_tool`
- The tool invocation lifecycle
- Giving your agent the ability to read repository files

You'll upgrade your Issue Reviewer to fetch and analyze referenced files automatically.

---

## Additional Resources

- 📚 [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- 📚 [Copilot SDK — System Message Customization](https://github.com/github/copilot-sdk/blob/main/python/README.md#system-message-customization)

---

**[← Back to Chapter 01](../01-structured-output/README.md)** | **[Continue to Chapter 03 →](../03-tool-calling/README.md)**
