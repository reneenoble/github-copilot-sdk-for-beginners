# Chapter 05 — Extracting Concepts & Mentoring Advice

![Chapter 5 banner illustration — an AI agent analyzing code and producing a mentoring report](./images/banner.png)

<!-- TODO: Add banner image to ./05-concepts-mentoring/images/banner.png — An illustration (1280×640) showing an AI agent with a magnifying glass over code, producing an output card with sections: "Concepts Required: JWT, OAuth, middleware" and "Mentoring Advice: Start with the token validation..." with a friendly mentor vibe. Same art style as course. -->

> **A great reviewer doesn't just classify — it teaches. Learn to extract concepts and provide mentoring advice that adapts to the learner's level.**

Your Issue Reviewer can already classify issues by difficulty and read referenced files. But a number alone isn't very helpful to a developer wondering *"Can I tackle this?"* In this chapter, you'll expand the reviewer to extract the specific concepts required and provide personalized mentoring guidance — transforming your tool from a simple classifier into a **development coach**.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 04: The Agent Loop & Streaming](../04-agent-loop-streaming/README.md)** first. You'll need familiarity with Pydantic models.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Design multi-field structured output schemas
- Extract required concepts and skills from code issues
- Generate mentoring advice tailored to difficulty level
- Use conditional generation to adjust tone and depth

> ⏱️ **Estimated Time**: ~40 minutes (10 min reading + 30 min hands-on)

---

# Generating Deeper Output

## 🧩 Real-World Analogy: The Adaptive Tutor

<img src="./images/analogy-adaptive-tutor.png" alt="Real-world analogy illustration — a tutor adjusting their teaching style for different students" width="800"/>

<!-- TODO: Add analogy image to ./05-concepts-mentoring/images/analogy-adaptive-tutor.png — An illustration showing one tutor at a whiteboard, with three students at different levels: a beginner getting simple diagrams, a mid-level student getting code examples, and an advanced student getting architecture diagrams. The tutor's speech bubbles adjust in complexity. Same art style as course. -->

Think about a great tutor — not one who gives every student the same lecture, but one who **adjusts to the learner**.

A first-year student asking about recursion gets: *"Think of Russian nesting dolls — each doll opens to reveal a smaller one, just like each function call opens a smaller version of the same problem."*

A graduate student asking about recursion gets: *"Consider the trade-offs between tail-recursive and continuation-passing styles in terms of stack frame allocation."*

Same topic. Completely different depth, vocabulary, and approach.

| Student Level | Tutor Behavior | Issue Reviewer Equivalent |
|---|---|---|
| First-year | Simple analogies, encouraging tone | Score 1-2: step-by-step guidance, beginner resources |
| Mid-level | Technical detail, some assumptions | Score 3: specific approach suggestions, relevant patterns |
| Graduate | Dense, precise, assumptions about background | Score 4-5: architecture considerations, trade-off analysis |

That's what conditional mentoring does. Your reviewer already knows the difficulty score — now it uses that score to adjust its advice, just like a tutor who checks the student's level before choosing how to explain.

---

# Key Concepts

Let's understand the building blocks before diving into code.

---

## Multi-Field Structured Output

In Chapter 1 you created a schema with `summary`, `difficulty_score`, and `recommended_level`. Now you'll add richer fields:

```python
from pydantic import BaseModel, Field
from typing import Literal


class IssueReview(BaseModel):
    summary: str = Field(description="One-sentence summary of the issue")
    difficulty_score: int = Field(ge=1, le=5, description="Difficulty 1-5")
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"] = Field(
        description="Recommended developer level"
    )
    concepts_required: list[str] = Field(
        description="List of technologies and concepts needed to solve this issue"
    )
    mentoring_advice: str = Field(
        description="Actionable advice tailored to the difficulty level"
    )
    files_analyzed: list[str] = Field(
        default_factory=list,
        description="Files the agent read during analysis"
    )
```

The key additions are:

- **`concepts_required`** — a list of specific skills like `["JWT validation", "middleware", "error handling"]`
- **`mentoring_advice`** — a paragraph of guidance that changes based on the difficulty level

---

## Conditional Generation

The model should adjust its mentoring style based on the difficulty:

| Difficulty | Audience | Mentoring Style |
|-----------|----------|----------------|
| 1–2 | Junior / Learning | Step-by-step guidance, explain concepts, suggest resources |
| 3 | Mid | Outline approach, mention key considerations, point to relevant patterns |
| 4–5 | Senior / Senior+ | High-level strategy, trade-off analysis, architecture considerations |

<img src="./images/mentoring-styles.png" alt="Visual comparison showing different mentoring styles for Junior vs Senior issues" width="800"/>

<!-- TODO: Add diagram to ./05-concepts-mentoring/images/mentoring-styles.png — A side-by-side comparison (800×400): LEFT shows a Junior issue (Score 1, "Fix typo in README") with friendly mentoring: "Great first issue! Open the file, find the typo, and submit a PR." RIGHT shows a Senior+ issue (Score 5, "Migrate auth to OAuth 2.0") with strategic mentoring: "Start by mapping the current auth flows. Consider backward compatibility..." Use speech bubble styling. -->

You achieve this through a well-designed system prompt:

```python
SYSTEM_PROMPT = """You are a GitHub issue reviewer and development mentor.

Analyze the issue and any referenced files, then respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<technology or skill>", ...],
  "mentoring_advice": "<guidance tailored to difficulty>",
  "files_analyzed": ["<files you read>"]
}

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.

## Concepts Extraction
List specific technologies, patterns, and skills. Be precise:
- ✅ "JWT token validation", "Python decorator pattern", "SQL injection prevention"
- ❌ "coding", "debugging", "programming" (too vague)

## Mentoring Advice Rules
- Score 1-2: Step-by-step guidance. Explain concepts. Suggest learning resources.
  Use encouraging, supportive tone.
- Score 3: Outline the approach. Mention patterns and considerations.
  Assume competence but provide direction.
- Score 4-5: High-level strategy. Discuss trade-offs and architecture.
  Treat as a peer discussion."""
```

---

## Concept Extraction Quality

Getting good concept extraction requires specificity in the prompt. Compare:

**Vague extraction:**
```json
{
  "concepts_required": ["security", "authentication", "Python"]
}
```

**Precise extraction:**
```json
{
  "concepts_required": [
    "JWT token validation",
    "Python datetime handling",
    "middleware chain pattern",
    "HTTP session management",
    "security vulnerability assessment"
  ]
}
```

The rubric in the system prompt — with ✅ and ❌ examples — guides the model toward precise extraction.

---

# See It In Action

> 💡 **About Example Outputs**: The sample outputs shown throughout this course are illustrative. Because AI responses vary each time, your results will differ in wording, formatting, and detail.

## The Mentor Reviewer

Here's the complete mentor reviewer. Create `concepts_mentor.py`:

```python
import asyncio
import json
import os
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
from typing import Literal


class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str
    files_analyzed: list[str] = Field(default_factory=list)


class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    repo_root = os.environ.get("REPO_PATH", ".")
    full_path = os.path.realpath(os.path.join(repo_root, params.file_path))
    if not full_path.startswith(os.path.realpath(repo_root)):
        return "Error: Access denied"
    try:
        with open(full_path, "r") as f:
            content = f.read()
            return content[:10_000] if len(content) > 10_000 else content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"


SYSTEM_PROMPT = """You are a GitHub issue reviewer and development mentor.

Analyze the issue and any referenced files, then respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<technology or skill>", ...],
  "mentoring_advice": "<guidance tailored to difficulty>",
  "files_analyzed": ["<files you read>"]
}

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.

## Concepts Extraction
List specific technologies, patterns, and skills. Be precise:
- Good: "JWT token validation", "Python decorator pattern"
- Bad: "coding", "debugging" (too vague)

## Mentoring Advice Rules
- Score 1-2: Step-by-step guidance. Explain concepts. Suggest resources.
- Score 3: Outline approach. Mention patterns and considerations.
- Score 4-5: High-level strategy. Discuss trade-offs and architecture."""


# --- Test Issues at Different Difficulty Levels ---

EASY_ISSUE = """
Title: Fix typo in README.md

The word "authentication" is misspelled as "authentification" on line 42
of the README.md file.
"""

HARD_ISSUE = """
Title: Migrate authentication system from session-based to OAuth 2.0

We need to migrate our entire authentication system from session-based auth
to OAuth 2.0 with support for Google, GitHub, and Microsoft providers.

This affects:
- src/auth/login.py (session handling → OAuth flow)
- src/auth/middleware.py (session checks → token validation)
- src/models/user.py (add OAuth fields)
- src/routes/callback.py (new file — OAuth callback handler)
- Database migration for OAuth tokens table
- All existing tests in tests/auth/

Must maintain backward compatibility during migration. Need to support
both auth methods during the transition period.
"""


async def review_issue(client, issue_text: str, label: str):
    """Review a single issue and display the results."""
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT
        },
        "tools": [get_file_contents],
        "streaming": True
    })

    # Show streaming progress
    session.on("tool.execution_start",
               lambda e: print(f"  🔧 Reading: {e.data.tool_name}"))

    print(f"\n{'═' * 60}")
    print(f"📋 Reviewing: {label}")
    print(f"{'═' * 60}\n")

    response = await session.send_and_wait({"prompt": issue_text})

    try:
        review = IssueReview.model_validate_json(response.data.content)
        print(f"  Summary: {review.summary}")
        print(f"  Difficulty: {review.difficulty_score}/5 "
              f"({review.recommended_level})")
        print(f"  Concepts: {', '.join(review.concepts_required)}")
        print(f"\n  💡 Mentoring Advice:")
        print(f"  {review.mentoring_advice}")
    except Exception as e:
        print(f"  ⚠️ Could not parse response: {e}")
        print(f"  Raw: {response.data.content[:200]}")


async def main():
    client = CopilotClient()
    await client.start()

    # Review two issues at very different difficulty levels
    await review_issue(client, EASY_ISSUE, "Easy Issue — Typo Fix")
    await review_issue(client, HARD_ISSUE, "Hard Issue — OAuth Migration")

    await client.stop()


asyncio.run(main())
```

## Expected Output

Running this produces two very different reviews:

![Terminal showing two issue reviews — one easy with simple advice, one hard with strategic advice](./images/mentoring-comparison.png)

<!-- TODO: Add screenshot to ./05-concepts-mentoring/images/mentoring-comparison.png — A terminal screenshot (dark theme) showing two reviews: (1) Easy issue: Score 1, concepts ["Markdown", "typo correction"], advice "Great first issue! Open README.md, find line 42..." (2) Hard issue: Score 5, concepts ["OAuth 2.0", "database migration", "backward compatibility"...], advice "Start by mapping current auth flows. Create a migration plan..." Show the contrast clearly. -->

<details>
<summary>🎬 See it in action!</summary>

![Mentor Reviewer Demo](./images/mentor-demo.gif)

<!-- TODO: Add GIF to ./05-concepts-mentoring/images/mentor-demo.gif — A terminal recording showing: (1) python concepts_mentor.py command, (2) both reviews displaying with contrasting mentoring advice. -->

*Demo output varies. Your results will differ from what's shown here.*

</details>

Notice how the mentoring advice changes dramatically:

- **Easy issue**: "Great first issue! Open the file, find the typo on line 42, and submit a PR."
- **Hard issue**: "Start by mapping all current auth flows. Design the OAuth integration layer with a clear interface boundary..."

---

# Practice

<img src="../images/practice.png" alt="Warm desk setup ready for hands-on practice" width="800"/>

Time to put what you've learned into action.

---

## ▶️ Try It Yourself

After completing the demos above, try these experiments to improve mentoring output:

1. **Add a Confidence Score** — Add a `confidence: int = Field(ge=1, le=5)` field to the schema. Include in the prompt:

   ```
   ## Confidence Score
   Rate how confident you are in your assessment (1-5):
   - 5: Clear issue, obvious classification
   - 3: Some ambiguity, reasonable assessment
   - 1: Very ambiguous, best guess
   ```

2. **Add Suggested Resources** — Add a `suggested_resources: list[str]` field and prompt the model to suggest relevant documentation, tutorials, or tools for the concepts required.

3. **Test Boundary Cases** — Create test issues that fall between difficulty levels (e.g., a "simple" bug that touches 4 files). See how the model handles ambiguity.

---

## 📝 Assignment

### Main Challenge: Build an Adaptive Mentor

Extend your Issue Reviewer to provide conditional mentoring:

1. Update the Pydantic schema with `concepts_required` and `mentoring_advice` fields

2. Create a system prompt with:
   - Clear difficulty rubric (1-5 scale)
   - Concept extraction guidelines (specific, not vague)
   - Conditional mentoring rules based on difficulty level

3. Test with issues at both ends of the difficulty spectrum

4. Compare the mentoring advice tone and depth

**Success criteria**: A Score 1 issue gets step-by-step, encouraging guidance. A Score 5 issue gets strategic, peer-level discussion of trade-offs.

See [assignment.md](./assignment.md) for full instructions.

<details>
<summary>💡 Hints</summary>

**Schema additions:**
```python
concepts_required: list[str] = Field(
    description="List of specific technologies and concepts needed"
)
mentoring_advice: str = Field(
    description="Actionable advice tailored to the difficulty level"
)
```

**Common issues:**
- Vague concepts like "security" or "coding" — add ✅/❌ examples in prompt
- Same mentoring tone for all levels — include explicit rules for each difficulty range
- Missing `files_analyzed` field when using tools — add with `default_factory=list`

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Vague concept extraction | Model returns "security" instead of "JWT validation" | Add specific ✅/❌ examples in system prompt |
| Same mentoring tone | Junior and Senior issues get identical advice style | Include explicit rules for each difficulty range |
| Missing `files_analyzed` | Pydantic validation fails when no tools used | Add `default_factory=list` to the field |
| Literal type mismatch | Model returns "senior" instead of "Senior" | Use exact casing in prompt examples |

### Troubleshooting

**"ValidationError: Input should be 'Junior', 'Mid', 'Senior' or 'Senior+'"** — The model returned a different casing or spelling. Make the system prompt explicit about exact values.

**Concepts are too vague** — Add more specific ✅/❌ examples in the system prompt. Show what good extraction looks like.

**Mentoring advice doesn't adapt** — Check that your difficulty rubric includes clear rules for each score range with tone guidance.

### Knowledge Check

<details>
<summary>Test your understanding</summary>

1. **Why use `Literal["Junior", "Mid", "Senior", "Senior+"]` instead of a plain `str`?**
   - a) It makes the code faster
   - b) It constrains the model to a fixed set of valid values
   - c) Pydantic requires it for all fields
   - d) It enables streaming

2. **What makes a good concept extraction?**
   - a) Listing broad categories like "programming" and "security"
   - b) Listing specific skills like "JWT validation" and "middleware patterns"
   - c) Listing only programming languages
   - d) Listing exactly 3 concepts every time

3. **How should mentoring advice differ for a Score 1 vs Score 5 issue?**
   - a) No difference — same tone for all levels
   - b) Score 1 gets step-by-step guidance; Score 5 gets high-level strategy
   - c) Score 1 gets more words; Score 5 gets fewer
   - d) Score 1 is formal; Score 5 is casual

**Answers:**
1. **b** — `Literal` constrains the model to only produce values from the specified set, ensuring validation catches unexpected values.
2. **b** — Specific, precise skills give actionable information. Vague categories aren't helpful for deciding if you can tackle an issue.
3. **b** — Junior issues get step-by-step, encouraging guidance. Senior+ issues get strategic, peer-level discussion of trade-offs.

</details>

</details>

---

# Summary

## 🔑 Key Takeaways

1. **Multi-field schemas capture richer data** — Beyond summary and difficulty, add concepts and mentoring advice for actionable output
2. **Precise concept extraction requires examples** — Show the model ✅/❌ examples of specific vs. vague concepts
3. **Conditional generation adapts to context** — Use the difficulty score to adjust mentoring tone and depth
4. **Pydantic validates complex structures** — Lists, Literals, and nested fields all work seamlessly

> 📚 **Glossary**: New to terms like "conditional generation" or "concept extraction"? See the [Glossary](../GLOSSARY.md) for definitions.

---

## 🏗️ Capstone Progress

Your Issue Reviewer is becoming a development coach!

| Chapter | Feature | Status |
|---------|---------|--------|
| 00 | Basic SDK setup & issue summarization | ✅ |
| 01 | Structured JSON output with Pydantic validation | ✅ |
| 02 | Reliable classification with prompt engineering | ✅ |
| 03 | Tool calling for file access | ✅ |
| 04 | Streaming UX & agent loop awareness | ✅ |
| **05** | **Concept extraction & mentoring advice** | **🔲 ← You are here** |
| 06 | RAG for large repositories | 🔲 |
| 07 | Safety & guardrails | 🔲 |
| 08 | Evaluation & testing | 🔲 |
| 09 | Production hardening & GitHub integration | 🔲 |

---

## ➡️ What's Next

Your reviewer now extracts concepts and provides mentoring — but what happens when an issue references 10 files, each with 5,000 lines?

In **[Chapter 06: Scaling with Retrieval (RAG)](../06-scaling-rag/README.md)**, you'll learn:

- Why context window limits matter for large repositories
- How to chunk files and create embeddings for semantic search
- Retrieving only the most relevant code for each query
- Injecting retrieved context into the agent's prompt

You'll handle enterprise-scale codebases without running out of context.

---

## Additional Resources

- 📚 [Pydantic Documentation — Models](https://docs.pydantic.dev/latest/concepts/models/)
- 📚 [Prompt Engineering — Few-shot Examples](https://platform.openai.com/docs/guides/prompt-engineering)

### 📚 Extra Reading: Agent Memory & Calibration

As your agent processes more issues, you might want it to learn from past decisions:

- **Short-term memory** — within a session, the model remembers tool results and previous reasoning
- **Long-term memory** — storing past reviews in a database and including them as context (not built into the SDK, but you can build it with tools)
- **Calibration** — comparing predicted difficulty with actual assignee seniority to improve accuracy over time
- **Confidence scoring** — using past accuracy to weight future predictions

This is advanced territory, but it's where AI agents become truly powerful.

### 🎁 Bonus Activity: Historical Difficulty Calibration

For an extra challenge:

1. Create a JSON file with 5 past issues and their actual assignee levels
2. Add a tool that reads this historical data
3. Include the historical data in the system prompt as calibration examples
4. Compare the model's predictions with and without historical context

This simulates how a production system would improve over time with feedback loops.

---

**[← Back to Chapter 04](../04-agent-loop-streaming/README.md)** | **[Continue to Chapter 06 →](../06-scaling-rag/README.md)**
