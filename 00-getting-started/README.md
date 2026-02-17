# Chapter 0 — Getting Started with the Copilot SDK

![Chapter 0 banner illustration — a developer at a terminal seeing their first AI response](./images/banner.png)

<!-- TODO: Add banner image to ./00-getting-started/images/banner.png — A warm, inviting illustration (1280×640) showing a developer at their terminal, with a speech bubble from an AI assistant displaying a friendly "Hello!" response. Use the same art style as the repo banner. -->

> *"The best way to learn is to start small — one prompt, one response, one 'aha!' moment."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Explain what the GitHub Copilot SDK is and how it differs from chat-based AI
- ✅ Install the SDK and verify your setup
- ✅ Send your first prompt and receive a response
- ✅ Understand the agent mental model (client → session → message)

## Pre-requisites

- Python 3.9+ installed
- A GitHub account with a Copilot subscription
- GitHub Copilot CLI installed ([Installation guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli))

---

## Introduction

Imagine you're a developer who reviews dozens of GitHub issues every day. Some are simple bug fixes, others require deep system knowledge. Wouldn't it be great if an AI assistant could read each issue, understand the codebase, and give you a structured analysis — automatically?

That's exactly what you'll build in this course, using the **GitHub Copilot SDK**.

The GitHub Copilot SDK lets you embed Copilot's agentic workflows directly into your applications. Instead of just chatting with an AI, you can give it **tools**, **instructions**, and **structure** — turning it into a programmable agent that plans, reasons, and takes actions.

In this first chapter, you'll install the SDK, send your first prompt, and see a response come back. It's that simple to get started.

## Key Concepts

### What Is the GitHub Copilot SDK?

The **GitHub Copilot SDK** is a programmable interface to the same engine behind the Copilot CLI. It exposes a production-tested agent runtime you can invoke from Python (also available in TypeScript, Go, and .NET).

![Diagram showing the SDK architecture: Your Python App → SDK Client → JSON-RPC → Copilot CLI (server mode)](./images/sdk-architecture.png)

<!-- TODO: Add diagram to ./00-getting-started/images/sdk-architecture.png — Architecture diagram showing: "Your Python App" → "CopilotClient (SDK)" → "JSON-RPC" → "Copilot CLI (server mode)" → "LLM". Use clean boxes and arrows. -->

Key things to know:

- The SDK communicates with the Copilot CLI via **JSON-RPC**.
- The SDK manages the CLI process lifecycle automatically.
- You authenticate through your GitHub account or a token.

### SDK vs. Chat Completion APIs

You may have used OpenAI's API or similar chat completion services. How is the Copilot SDK different?

| Feature | Chat Completion API | Copilot SDK |
|---------|-------------------|-------------|
| **Purpose** | Single request/response | Agent workflows with planning |
| **Tools** | You implement tool loop | Built-in tool orchestration |
| **File access** | Manual | Built-in file tools |
| **Authentication** | API key | GitHub Copilot subscription |
| **Orchestration** | You build it | SDK handles planning, tool calls, retries |

> 💡 **Tip:** Think of the Copilot SDK as a "batteries-included" agent framework — you define what the agent should do, and Copilot handles the how.

### The Agent Mental Model

Working with the SDK follows a simple three-step pattern:

1. **Create a Client** — connects to the Copilot CLI server.
2. **Create a Session** — an ongoing conversation with a model.
3. **Send Messages** — prompts that the agent responds to.

```
CopilotClient (manages connection)
  └── CopilotSession (a conversation)
        └── send() / sendAndWait() (messages)
              └── Events (responses, tool calls, streaming)
```

### Basic Message Structure

When you send a message, the SDK:

1. Delivers your prompt to the model
2. The model generates a response (potentially calling tools)
3. Events are emitted back to your code
4. The session becomes idle when processing completes

---

## Demo / Code Walkthrough

Let's write your first Copilot SDK program. This minimal example sends a prompt and prints the response.

### Step 1: Set Up Your Project

```bash
mkdir copilot-issue-reviewer && cd copilot-issue-reviewer
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install github-copilot-sdk
```

### Step 2: Verify the Copilot CLI

```bash
copilot --version
```

You should see a version number. If not, follow the [Copilot CLI installation guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli).

### Step 3: Your First Agent

Create a file called `hello_agent.py`:

```python
import asyncio
from copilot import CopilotClient


async def main():
    # Step 1: Create a client (connects to Copilot CLI)
    client = CopilotClient()
    await client.start()

    # Step 2: Create a session (a conversation with a model)
    session = await client.create_session({"model": "gpt-4.1"})

    # Step 3: Send a message and wait for the response
    response = await session.send_and_wait({"prompt": "What is 2 + 2?"})

    # Print the response
    print(response.data.content)

    # Clean up
    await session.destroy()
    await client.stop()


asyncio.run(main())
```

Run it:

```bash
python hello_agent.py
```

You should see:

```
4
```

🎉 **Congratulations!** You've just run your first Copilot SDK agent.

### Step 4: Try a Concept Demo

Now let's try something more relevant to our capstone — asking the model to summarize a GitHub issue description:

```python
import asyncio
from copilot import CopilotClient


SAMPLE_ISSUE = """
Title: Login page crashes on mobile Safari

When users try to log in using Safari on iOS 17, the page crashes after
clicking the "Sign In" button. The error in the console shows:
TypeError: Cannot read properties of undefined (reading 'focus')

This happens because the autofocus directive is trying to reference a
DOM element that hasn't rendered yet on mobile browsers.

Steps to reproduce:
1. Open the app on iOS Safari
2. Navigate to /login
3. Enter credentials and click "Sign In"
4. Page crashes with white screen
"""


async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({"model": "gpt-4.1"})

    response = await session.send_and_wait({
        "prompt": f"Summarize this GitHub issue in 2-3 sentences:\n\n{SAMPLE_ISSUE}"
    })

    print("Issue Summary:")
    print(response.data.content)

    await session.destroy()
    await client.stop()


asyncio.run(main())
```

![Screenshot of terminal output showing the issue summary response](./images/terminal-output.png)

<!-- TODO: Add screenshot to ./00-getting-started/images/terminal-output.png — A terminal screenshot showing the output of the concept demo script: "Issue Summary:" followed by a 2-3 sentence AI-generated summary of the sample issue. Show a clean terminal with readable text. -->

> 💡 **Try it yourself:** Modify the `SAMPLE_ISSUE` text with a real issue from one of your GitHub repositories and see how the summary changes.

---

## 🧠 Knowledge Check

1. What protocol does the Copilot SDK use to communicate with the CLI?
   - A) HTTP REST
   - B) JSON-RPC ✅
   - C) GraphQL

2. What is the correct order of operations when using the SDK?
   - A) Send message → Create session → Create client
   - B) Create client → Create session → Send message ✅
   - C) Create session → Create client → Send message

3. What does `send_and_wait()` do?
   - A) Sends a message and returns immediately
   - B) Sends a message and waits until the session is idle, then returns the response ✅
   - C) Sends multiple messages in parallel

---

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| **00** | **Basic issue summary** | **🔲 ← You are here** |
| 01 | Structured output | 🔲 |
| 02 | Reliable classification | 🔲 |
| 03 | Tool calling (file fetch) | 🔲 |
| 04 | Streaming UX | 🔲 |
| 05 | Concepts & mentoring | 🔲 |
| 06 | RAG for large repos | 🔲 |
| 07 | Safety & guardrails | 🔲 |
| 08 | Evaluation & testing | 🔲 |
| 09 | Production hardening | 🔲 |

**Your task:** Create a simple CLI tool that accepts a GitHub issue description and prints a summary.

See [assignment.md](./assignment.md) for full instructions.

---

## Additional Resources

- 📖 [GitHub Copilot SDK Repository](https://github.com/github/copilot-sdk)
- 📖 [Python SDK Reference](https://github.com/github/copilot-sdk/blob/main/python/README.md)
- 📖 [Getting Started Guide](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md)
- 📖 [Copilot CLI Installation](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)

---

## Next Steps

In the next lesson, you'll learn how to **constrain the model's output using schemas** — so instead of free-form text, you get structured, machine-readable JSON. → [Chapter 1 — Structured Output](../01-structured-output/README.md)
