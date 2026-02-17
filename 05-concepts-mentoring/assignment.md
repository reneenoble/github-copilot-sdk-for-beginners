# Assignment — Extracting Concepts & Mentoring Advice

## Objectives

Expand your Issue Reviewer to extract required concepts and generate difficulty-appropriate mentoring advice.

## What You'll Build

An enhanced Issue Reviewer that produces:

1. **Concepts required** — a list of specific technologies and skills
2. **Mentoring advice** — guidance tailored to the issue's difficulty level
3. **Side-by-side comparison** — review an easy and a hard issue to see the difference

## Instructions

### Step 1 — Expand the Pydantic Schema

Open `code/concepts_mentor.py`. Add `concepts_required` (list of strings) and `mentoring_advice` (string) fields to the `IssueReview` model.

### Step 2 — Write the System Prompt

Create a system prompt that includes:

- A difficulty rubric (Score 1-5 with descriptions)
- Concept extraction rules (specific, not vague)
- Mentoring advice rules (different tone per difficulty tier)

### Step 3 — Review Multiple Issues

Use the provided test issues to review at least one easy and one hard issue. Parse the JSON output and display each field clearly.

### Step 4 — Compare Mentoring Styles

Print the results side by side and observe how the mentoring advice changes. The easy issue should receive step-by-step guidance, while the hard issue should receive strategic advice.

## Stretch Goals

- 🌟 Add a `confidence: int` field (1-5) with scoring criteria in the prompt
- 🌟 Add a `suggested_resources: list[str]` field for learning links
- 🌟 Create a boundary test case (ambiguous difficulty) and review it 3 times to check consistency
- 🌟 Add historical calibration data via a `get_past_reviews` tool

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Schema expanded | `IssueReview` includes `concepts_required` and `mentoring_advice` |
| Precise concepts | Extracted concepts are specific (not vague like "coding") |
| Mentoring varies | Easy issues get step-by-step advice; hard issues get strategic advice |
| Multiple issues | At least 2 issues at different difficulty levels are reviewed |
| Valid output | All responses parse successfully into the Pydantic model |
