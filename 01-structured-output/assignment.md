# Assignment: Structured Issue Analysis

## Objectives

After completing this assignment, you will have:
- [ ] Extended the Issue Reviewer to return structured JSON output
- [ ] Defined a Pydantic model for validation
- [ ] Handled parsing and validation errors gracefully

## Instructions

### Step 1: Define Your Schema

Create a Pydantic model called `IssueAnalysis` with these fields:
- `summary` (str) — a one-sentence summary
- `difficulty_score` (int) — 1 to 5
- `recommended_level` (str) — "Junior", "Mid", "Senior", or "Senior+"

### Step 2: Craft Your System Prompt

Write a system message that instructs the model to return ONLY a JSON object matching your schema. Be explicit about the allowed values.

### Step 3: Parse and Validate

Use `json.loads()` and your Pydantic model to parse and validate the response. Print each field on its own line.

### Step 4: Test with Multiple Issues

Try your script with at least 3 different issues of varying complexity:
- A simple typo fix
- A medium feature request
- A complex architecture issue

Verify that the difficulty scores make sense.

## Stretch Goals (Optional)
- 🌟 Add a new field `estimated_hours` (float) to the schema
- 🌟 Break the schema intentionally (e.g., remove a required field from the prompt) and observe what the model returns
- 🌟 Add retry logic that re-sends the prompt if validation fails

## Rubric

| Criteria | Complete |
|----------|----------|
| Pydantic model defined with correct types | ✅ |
| System message requests JSON output | ✅ |
| Response is parsed and validated | ✅ |
| Errors are handled with try/except | ✅ |
| Tested with multiple issues | ⭐ (bonus) |
