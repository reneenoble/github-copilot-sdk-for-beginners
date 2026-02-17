# Assignment — Evaluation & Testing

## Objectives

Build a test harness that measures your Issue Reviewer's accuracy, consistency, and schema validity.

## What You'll Build

A test harness that:

1. **Defines golden test cases** — issues with known expected difficulty scores and levels
2. **Runs accuracy tests** — compares predictions to expected values
3. **Runs consistency tests** — checks if the same input produces the same output across runs
4. **Validates schemas** — ensures every response parses into the Pydantic model
5. **Reports results** — prints a clear summary with pass/fail metrics

## Instructions

### Step 1 — Define Golden Test Cases

Open `code/test_harness.py`. Create at least 5 golden test cases spanning all difficulty levels (1 through 5). Each should have a name, issue text, expected score, and expected level.

### Step 2 — Implement Run Review

Complete the `run_review` function that sends an issue to the SDK and parses the response into an `IssueReview` model.

### Step 3 — Build Accuracy Testing

Complete the `run_accuracy_tests` function that runs each golden test, compares the result to the expected values, and reports exact matches and close matches (±1).

### Step 4 — Build Consistency Testing

Complete the `run_consistency_tests` function that runs a subset of tests 3 times each and reports whether the scores and levels are consistent.

### Step 5 — Review Results

Run the full test suite and interpret the results. Are any tests consistently wrong? Is the model stable on boundary cases?

## Stretch Goals

- 🌟 Save baseline results to `baseline.json` and implement drift detection
- 🌟 Test concept extraction quality (no vague terms like "coding")
- 🌟 Add boundary test cases (issues between difficulty levels)
- 🌟 Generate an HTML report with pass/fail styling
- 🌟 Integrate with `pytest` so tests run with `pytest test_harness.py`

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Golden tests | At least 5 test cases spanning difficulty levels 1–5 |
| Accuracy report | Shows exact match %, close match %, and schema validity |
| Consistency test | At least 2 tests run 3× each with consistency reported |
| Schema validation | Every response is validated against the Pydantic model |
| Clear output | Results are easy to read with pass/fail indicators |
