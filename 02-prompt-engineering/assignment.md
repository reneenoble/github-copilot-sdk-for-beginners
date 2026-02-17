# Assignment: Build a Reliable Classifier

## Objectives

After completing this assignment, you will have:
- [ ] A system prompt with a clear difficulty rubric
- [ ] At least 2 few-shot examples in the prompt
- [ ] Validation that only allowed values are returned
- [ ] Consistent classification across multiple runs

## Instructions

### Step 1: Create a Rubric

Write a 5-level difficulty rubric that maps issue characteristics to scores 1–5. Include specific, observable criteria (file count, complexity, domain knowledge needed).

### Step 2: Add Few-Shot Examples

Add 2–3 examples covering easy (score 1–2), medium (score 3), and hard (score 4–5) issues.

### Step 3: Constrain Values

Explicitly list allowed values for `recommended_level` and instruct the model to use ONLY those values.

### Step 4: Test Consistency

Run the same issue through your classifier 3 times. All 3 runs should produce the same `difficulty_score` and `recommended_level`.

## Stretch Goals (Optional)
- 🌟 Add a `reasoning` field that requires the model to explain its classification before scoring (chain-of-thought)
- 🌟 Compare results across different models (`gpt-4.1` vs `claude-sonnet-4.5`)
- 🌟 Test with 5 different issues and verify the rubric produces sensible scores for each

## Rubric

| Criteria | Complete |
|----------|----------|
| System prompt includes a difficulty rubric | ✅ |
| At least 2 few-shot examples included | ✅ |
| Allowed values explicitly listed | ✅ |
| 3 runs of the same issue produce consistent results | ✅ |
| Stretch goal attempted | ⭐ (bonus) |
