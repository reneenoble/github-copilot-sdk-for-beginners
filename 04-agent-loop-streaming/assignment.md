# Assignment — The Agent Loop & Streaming UX

## Objectives

In this assignment, you'll add streaming to your Issue Reviewer so it provides real-time feedback as it processes an issue.

## What You'll Build

An enhanced Issue Reviewer that:

1. **Streams** the response text progressively to the terminal
2. **Displays tool activity** — shows when tools are called and when they complete
3. **Reports timing** — shows elapsed time and total tool calls at the end
4. **Includes a status reporter** — uses a class to track progress

## Instructions

### Step 1 — Enable Streaming

Open `code/streaming_reviewer.py`. Enable streaming in the session configuration.

### Step 2 — Register Event Listeners

Register listeners for:

- `assistant.message_delta` — print each text chunk as it arrives
- `assistant.message` — print a completion message
- `tool.execution_start` — show which tool is being called
- `tool.execution_complete` — confirm the tool finished

### Step 3 — Build a StatusReporter

Create a `StatusReporter` class that:

- Tracks elapsed time from when it was created
- Counts the number of tool calls
- Provides a summary when the response is complete

### Step 4 — Test with a Multi-File Issue

Use the sample issue that references two files. Observe the agent loop making multiple tool calls before generating the response.

## Stretch Goals

- 🌟 Add a `session.idle` listener that prints a final "all done" message
- 🌟 Add a `on_reasoning_delta` listener for `assistant.reasoning_delta` events (if supported by the model)
- 🌟 Track the total characters received via streaming and compare with the final response length
- 🌟 Add a progress spinner that animates while waiting for tool results

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Streaming enabled | `streaming: True` is set in session config |
| Delta listener | `assistant.message_delta` events print text progressively |
| Tool listeners | `tool.execution_start` and `tool.execution_complete` show tool activity |
| StatusReporter | A class tracks time, tool count, and prints a summary |
| Clean output | Terminal output is readable with clear formatting |
