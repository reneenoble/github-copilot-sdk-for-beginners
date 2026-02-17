# Glossary

Quick reference for technical terms used throughout this course. Don't worry about memorizing these now — refer back as needed.

---

## A

### Agent

An AI system that can reason, plan, and take actions to accomplish tasks. In the Copilot SDK, agents combine prompts, tools, and iteration to solve multi-step problems autonomously.

### Agent Loop

The iterative cycle where an agent: (1) receives input, (2) decides whether to call a tool or respond, (3) processes tool results, and (4) repeats until done. The SDK handles this loop automatically.

### Async/Await

Python syntax for asynchronous programming. `async def` defines a coroutine, and `await` pauses execution until a result is ready. Required for the Copilot SDK since it uses non-blocking I/O.

---

## C

### Chunking

Splitting large text (like source files) into smaller pieces to fit within context window limits. Common strategies include splitting by lines, functions, or semantic boundaries.

### Client

The `CopilotClient` class that manages the connection to the Copilot CLI server. You create one client, then create sessions from it.

### Context Window

The maximum amount of text (measured in tokens) that a model can process at once. When you add files, conversation history, and system prompts, they all consume context window space.

### Copilot CLI

The command-line interface for GitHub Copilot that runs as a background server. The SDK communicates with it via JSON-RPC.

---

## D

### Dataclass

A Python decorator (`@dataclass`) that automatically generates `__init__`, `__repr__`, and other methods for classes that primarily store data. Used throughout this course for defining schemas.

### Determinism

The property of producing the same output for the same input. Lower temperature settings make model outputs more deterministic.

---

## E

### Embeddings

Numerical vector representations of text that capture semantic meaning. Similar texts have similar embeddings, enabling semantic search and retrieval.

### Event

A notification from the SDK about something that happened during processing — like a tool being called, text being streamed, or an error occurring. You register handlers to respond to events.

---

## F

### Few-Shot Prompting

Including example input/output pairs in your prompt to demonstrate the desired behavior. Typically 2-5 examples are sufficient.

---

## G

### Golden Test

A test case with a known expected output, used to verify that the model produces correct results. Essential for evaluating AI system reliability.

### Guardrails

Safety measures that protect AI systems from misuse — including prompt injection defenses, input validation, output validation, and access controls.

---

## H

### Hallucination

When a model generates plausible-sounding but factually incorrect information. Structured output and validation help detect hallucinations.

### Hook

A callback function that the SDK calls at specific points during processing. `on_pre_tool_use` lets you inspect and approve/reject tool calls before they execute.

---

## I

### Iteration Limit

A cap on how many times the agent loop can run, preventing infinite loops. Set via system prompt guidance or SDK configuration.

---

## J

### JSON-RPC

A remote procedure call protocol using JSON. The Copilot SDK uses JSON-RPC to communicate between your Python code and the Copilot CLI server.

---

## M

### Message

A single prompt sent to the model within a session. Messages can include text, file references, and other context.

---

## P

### Prompt Engineering

The practice of crafting effective prompts to get reliable, consistent outputs from AI models. Includes techniques like rubrics, few-shot examples, and explicit constraints.

### Prompt Injection

An attack where malicious input attempts to override the system prompt and make the model behave unexpectedly. Defense requires hardened system prompts and input validation.

### Pydantic

A Python library for data validation using type annotations. Used throughout this course to define schemas and validate model outputs.

---

## R

### RAG

Retrieval-Augmented Generation. A technique that retrieves relevant information from a knowledge base and injects it into the prompt, enabling AI to answer questions about specific documents or codebases.

### Rubric

A scoring guide included in the system prompt that defines criteria for classification. Rubrics improve consistency by giving the model explicit rules to follow.

---

## S

### Schema

A definition of the structure and types of data. In this course, schemas define the shape of model outputs using Pydantic models or JSON Schema.

### Session

A `CopilotSession` object representing an ongoing conversation with a model. Sessions maintain context across multiple messages and can be configured with system prompts, tools, and streaming settings.

### Streaming

Receiving model output incrementally as it's generated, rather than waiting for the complete response. Enables responsive UIs that show progress in real-time.

### System Prompt

Instructions given to the model that define its persona, rules, and constraints. Placed at the beginning of the conversation and apply to all subsequent messages.

---

## T

### Temperature

A parameter controlling randomness in model outputs. Low temperature (0.0-0.3) produces more deterministic, consistent results. High temperature (0.7-1.0) produces more creative, varied outputs.

### Token

A unit of text that AI models process. Roughly 4 characters or 0.75 words in English. Used to measure both input (prompts) and output (responses).

### Tool

A function you expose to the model that it can choose to call when it needs additional information or capabilities. Defined with `@define_tool` decorator and Pydantic schemas.

### Top-k Retrieval

A retrieval strategy that returns the k most relevant items (e.g., code chunks) based on similarity to a query.

---

## V

### Validation

Checking that data conforms to expected rules. In this course, Pydantic validates that model outputs match your schema, catching malformed or unexpected responses.

---

*This glossary covers terms used in the GitHub Copilot SDK for Beginners course. For general AI/ML terminology, see the [Generative AI for Beginners glossary](https://github.com/microsoft/generative-ai-for-beginners).*
