# Assignment: Your First Issue Summarizer

## Objectives

After completing this assignment, you will have:
- [ ] A working Python script that uses the Copilot SDK
- [ ] Experience sending prompts and receiving responses
- [ ] The foundation of the capstone Issue Reviewer project

## Instructions

### Step 1: Create the Project Structure

```bash
mkdir -p capstone/
cd capstone/
```

Create a file called `issue_summary.py`.

### Step 2: Build the Summarizer

Write a script that:

1. Creates a `CopilotClient` and starts it
2. Creates a session with the `gpt-4.1` model
3. Defines a hardcoded GitHub issue (you can use the sample from the lesson, or copy a real issue)
4. Sends the issue to the model with a prompt asking for a summary
5. Prints the summary to the terminal
6. Cleans up the session and client

### Step 3: Experiment

Try the following modifications (one at a time):

1. **Change the prompt** — Instead of "Summarize this issue", try "What is the root cause of this issue?"
2. **Add system instructions** — Use the `system_message` parameter in `create_session` to give the model a persona (e.g., "You are a senior software engineer reviewing GitHub issues.")
3. **Try a different question** — Ask the model to suggest a fix for the issue
4. **Inspect the response** — Print `response.type`, `response.data`, and explore the response object structure

## Expected Output

```
$ python issue_summary.py
Issue Summary:
The login page crashes on mobile Safari (iOS 17) when users click "Sign In"
due to a TypeError caused by an autofocus directive referencing an unrendered
DOM element. The fix would involve deferring the autofocus until after the
component has fully mounted.
```

## Stretch Goals (Optional)

- 🌟 Accept the issue text from a file instead of hardcoding it: `python issue_summary.py --file issue.txt`
- 🌟 Accept the issue text from stdin: `echo "Bug: ..." | python issue_summary.py`
- 🌟 Add a `--question` flag to customize what you ask about the issue

## Rubric

| Criteria | Complete |
|----------|----------|
| Script runs without errors | ✅ |
| Uses `CopilotClient` and `create_session` correctly | ✅ |
| Sends a prompt and prints a response | ✅ |
| Properly cleans up (destroy session, stop client) | ✅ |
| Experimented with at least one modification | ⭐ (bonus) |
| Stretch goal attempted | ⭐ (bonus) |
