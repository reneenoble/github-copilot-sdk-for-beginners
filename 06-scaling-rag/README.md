# Chapter 6 — Scaling with Retrieval (RAG)

![Chapter 6 banner illustration — a large codebase being filtered through a funnel into a small context window](./images/banner.png)

<!-- TODO: Add banner image to ./06-scaling-rag/images/banner.png — An illustration (1280×640) showing a large repository (many folders/files) on the left, passing through a funnel labeled "Retrieval" that filters down to a small context window on the right containing only the relevant chunks. An AI agent sits at the right side, reading from the small context. Same art style as course. -->

> *"You can't send the entire codebase to the model — but you can send the right parts."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Explain why context window limits matter for large repositories
- ✅ Chunk large files into smaller pieces
- ✅ Create simple embeddings for semantic search
- ✅ Retrieve the most relevant chunks for a given query
- ✅ Inject retrieved context into the agent's prompt

## Pre-requisites

- Completed [Chapter 5 — Concepts & Mentoring](../05-concepts-mentoring/README.md)
- `pip install numpy` (for similarity computation)

---

## Introduction

Your Issue Reviewer uses the `get_file_contents` tool to read files. That works great for small files — but what happens when a file is 5,000 lines long? Or when the issue references 10 files?

You'll hit the model's **context window limit**. Every model has a maximum number of tokens it can process at once. If you exceed it, the API will return an error or the model will ignore some of the input.

**Retrieval-Augmented Generation (RAG)** solves this by:

1. Splitting files into smaller **chunks**
2. Creating **embeddings** (numerical representations) of each chunk
3. When the agent needs context, **searching** for the most relevant chunks
4. Injecting only the **top results** into the prompt

![Diagram showing the RAG pipeline: Chunk → Embed → Store → Query → Retrieve → Inject](./images/rag-pipeline.png)

<!-- TODO: Add diagram to ./06-scaling-rag/images/rag-pipeline.png — A horizontal pipeline diagram (1000×300): (1) "Large file" → (2) "Split into chunks" (showing file split into colored blocks) → (3) "Create embeddings" (blocks become vectors) → (4) "Store in index" (vectors in a grid) → (5) "Query: issue text" → (6) "Retrieve top-k" (nearest vectors highlighted) → (7) "Inject into prompt" (chunks go into the agent). -->

---

## Key Concepts

### Context Window Limits

Models have a fixed context window:

| Model | Context Window |
|-------|---------------|
| gpt-4.1 | 128K tokens |
| gpt-5 | 128K tokens |
| claude-sonnet-4.5 | 200K tokens |

That sounds like a lot, but consider:

- 1 token ≈ 4 characters of code
- A 2,000-line Python file ≈ 15,000–25,000 tokens
- 5 files = 75,000–125,000 tokens
- Plus the system prompt, issue text, and conversation history

You can run out of space quickly.

### Chunking Strategies

Splitting files into chunks requires strategy. Naive approaches (split every N characters) can break functions in half. Better approaches respect code structure:

```python
def chunk_by_lines(content: str, chunk_size: int = 50, overlap: int = 5) -> list[dict]:
    """Split content into chunks of approximately chunk_size lines with overlap."""
    lines = content.split("\n")
    chunks = []

    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        chunks.append({
            "content": "\n".join(chunk_lines),
            "start_line": i + 1,
            "end_line": min(i + chunk_size, len(lines)),
        })

    return chunks
```

> 💡 **Tip**: Overlap between chunks ensures that a function split across chunk boundaries still appears (at least partially) in both chunks.

### Simple Embeddings with the SDK

You can use the Copilot SDK to create embeddings via a tool, or for simplicity, use a lightweight approach — keyword-based similarity:

```python
import re
from collections import Counter


def simple_embed(text: str) -> Counter:
    """Create a simple bag-of-words embedding."""
    words = re.findall(r'\b[a-z_][a-z0-9_]*\b', text.lower())
    return Counter(words)


def similarity(embed_a: Counter, embed_b: Counter) -> float:
    """Compute cosine similarity between two bag-of-words embeddings."""
    common = set(embed_a.keys()) & set(embed_b.keys())
    if not common:
        return 0.0
    
    dot_product = sum(embed_a[w] * embed_b[w] for w in common)
    mag_a = sum(v ** 2 for v in embed_a.values()) ** 0.5
    mag_b = sum(v ** 2 for v in embed_b.values()) ** 0.5
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)
```

For production systems, you'd use proper embedding models (e.g., via an embedding API), but this bag-of-words approach is enough to demonstrate the concept.

### Top-k Retrieval

Given a query and a set of embedded chunks, retrieve the `k` most similar:

```python
def retrieve_top_k(query: str, chunks: list[dict], k: int = 3) -> list[dict]:
    """Retrieve the k most relevant chunks for a query."""
    query_embed = simple_embed(query)
    
    scored = []
    for chunk in chunks:
        chunk_embed = simple_embed(chunk["content"])
        score = similarity(query_embed, chunk_embed)
        scored.append({**chunk, "score": score})
    
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:k]
```

### Building a RAG-Enhanced Tool

Instead of returning the full file, your tool can now return only the relevant chunks:

```python
class ChunkIndex:
    """In-memory index of file chunks for retrieval."""
    
    def __init__(self):
        self.chunks: list[dict] = []
    
    def add_file(self, file_path: str, content: str):
        for chunk in chunk_by_lines(content, chunk_size=50, overlap=5):
            chunk["file_path"] = file_path
            self.chunks.append(chunk)
    
    def search(self, query: str, k: int = 3) -> list[dict]:
        return retrieve_top_k(query, self.chunks, k)
```

---

## Demo Walkthrough

Let's build a RAG-enhanced reviewer. Create `rag_reviewer.py`:

```python
import asyncio
import json
import os
import re
from collections import Counter
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
from typing import Literal


# --- Chunking & Retrieval ---

def chunk_by_lines(content: str, chunk_size: int = 50, overlap: int = 5):
    lines = content.split("\n")
    chunks = []
    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        chunks.append({
            "content": "\n".join(chunk_lines),
            "start_line": i + 1,
            "end_line": min(i + chunk_size, len(lines)),
        })
    return chunks


def simple_embed(text: str) -> Counter:
    words = re.findall(r'\b[a-z_][a-z0-9_]*\b', text.lower())
    return Counter(words)


def similarity(embed_a: Counter, embed_b: Counter) -> float:
    common = set(embed_a.keys()) & set(embed_b.keys())
    if not common:
        return 0.0
    dot_product = sum(embed_a[w] * embed_b[w] for w in common)
    mag_a = sum(v ** 2 for v in embed_a.values()) ** 0.5
    mag_b = sum(v ** 2 for v in embed_b.values()) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)


class ChunkIndex:
    def __init__(self):
        self.chunks = []

    def add_file(self, file_path: str, content: str):
        for chunk in chunk_by_lines(content):
            chunk["file_path"] = file_path
            self.chunks.append(chunk)
        print(f"  📦 Indexed {file_path} "
              f"({len(chunk_by_lines(content))} chunks)")

    def search(self, query: str, k: int = 3):
        query_embed = simple_embed(query)
        scored = []
        for chunk in self.chunks:
            score = similarity(query_embed, simple_embed(chunk["content"]))
            scored.append({**chunk, "score": score})
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:k]


# --- Global index ---
index = ChunkIndex()


# --- Tool Definitions ---

class SearchParams(BaseModel):
    query: str = Field(description="Search query to find relevant code")


@define_tool(description="Search the repository for code relevant to a query. "
             "Returns the most relevant code chunks.")
async def search_code(params: SearchParams) -> str:
    results = index.search(params.query, k=3)
    if not results:
        return "No relevant code found."

    output = []
    for r in results:
        output.append(
            f"--- {r['file_path']} (lines {r['start_line']}-{r['end_line']}, "
            f"relevance: {r['score']:.2f}) ---\n{r['content']}"
        )
    return "\n\n".join(output)


# --- Schema ---

class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str
    chunks_used: int = Field(description="Number of code chunks retrieved")


SYSTEM_PROMPT = """You are a GitHub issue reviewer with access to a code search tool.

Use the search_code tool to find relevant code. The tool returns the most
relevant code chunks — you don't need to read entire files.

Respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<specific skill>", ...],
  "mentoring_advice": "<guidance>",
  "chunks_used": <number of chunks you reviewed>
}
"""


async def main():
    # Pre-index some repository files
    repo_root = os.environ.get("REPO_PATH", ".")
    print("📂 Indexing repository...\n")

    for root, dirs, files in os.walk(repo_root):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("node_modules", "__pycache__", ".git", "venv")]
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".md")):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, repo_root)
                try:
                    with open(path, "r") as fh:
                        content = fh.read()
                    index.add_file(rel_path, content)
                except Exception:
                    pass

    print(f"\n✅ Indexed {len(index.chunks)} total chunks\n")

    # --- Review an issue ---
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT
        },
        "tools": [search_code],
        "streaming": True
    })

    session.on("tool.execution_start",
               lambda e: print(f"  🔍 Searching: {e.data.tool_name}"))
    session.on("tool.execution_complete",
               lambda e: print(f"  ✅ Search complete\n"))

    issue = """
    Title: Fix token expiry validation in auth system

    The validate_token() function doesn't check the 'exp' claim.
    Expired JWT tokens are accepted by the login handler.
    This is a security vulnerability affecting authentication.
    """

    print("📋 Sending issue for review...\n")
    response = await session.send_and_wait({"prompt": issue})

    try:
        review = IssueReview.model_validate_json(response.data.content)
        print(f"\n  📝 {review.summary}")
        print(f"  📊 Difficulty: {review.difficulty_score}/5")
        print(f"  🧠 Concepts: {', '.join(review.concepts_required)}")
        print(f"  📦 Chunks used: {review.chunks_used}")
        print(f"  💡 Advice: {review.mentoring_advice}")
    except Exception as e:
        print(f"  ⚠️ Parse error: {e}")
        print(f"  Raw: {response.data.content[:300]}")

    await client.stop()


asyncio.run(main())
```

### Running the Demo

```bash
REPO_PATH=./my-repo python rag_reviewer.py
```

You'll see output like:

```
📂 Indexing repository...

  📦 Indexed src/auth/login.py (4 chunks)
  📦 Indexed src/auth/tokens.py (2 chunks)
  📦 Indexed src/auth/middleware.py (3 chunks)

✅ Indexed 42 total chunks

📋 Sending issue for review...

  🔍 Searching: search_code
  ✅ Search complete

  📝 Token expiry validation missing in auth system
  📊 Difficulty: 4/5
  🧠 Concepts: JWT validation, token expiry, middleware security
  📦 Chunks used: 3
  💡 Advice: Review the validate_token() function...
```

### Full File vs RAG Comparison

| Approach | Tokens Used | Files Supported | Speed |
|----------|------------|----------------|-------|
| Full file injection | ~15K per file | 3-5 files max | Slower |
| RAG (top-3 chunks) | ~2K total | Unlimited | Faster |

The RAG approach uses roughly **7× fewer tokens** while often finding the most relevant code.

---

## Practice: Experimenting with RAG

### 1. Compare Full-File vs RAG

Modify the tool to return the full file content. Run the same issue with both approaches and compare:

- Token usage (character count as a proxy)
- Response quality
- Speed

### 2. Tune Chunk Size

Try different chunk sizes (20, 50, 100 lines) and observe:

- Smaller chunks → more precise retrieval but less context
- Larger chunks → more context but less precision

### 3. Add Metadata to Chunks

Enhance chunks with metadata like function names, class names, or import statements. This can improve retrieval accuracy:

```python
def enhanced_chunk(content: str, file_path: str, start_line: int):
    # Extract function/class names from the chunk
    definitions = re.findall(r'^(?:def|class)\s+(\w+)', content, re.MULTILINE)
    return {
        "content": content,
        "file_path": file_path,
        "start_line": start_line,
        "definitions": definitions,
    }
```

---

## Knowledge Check ✅

1. **Why can't you send entire large files to the model?**
   - a) The model doesn't understand code
   - b) Large files exceed the context window token limit
   - c) The SDK doesn't support file reading
   - d) Python files can't be converted to tokens

2. **What does "top-k retrieval" mean?**
   - a) Retrieving the k largest files
   - b) Retrieving the k most recently modified chunks
   - c) Retrieving the k most relevant chunks based on similarity
   - d) Retrieving the first k chunks of each file

3. **Why use overlapping chunks?**
   - a) It makes the index smaller
   - b) It ensures functions split at boundaries appear in both adjacent chunks
   - c) It reduces token usage
   - d) The SDK requires it

<details>
<summary>Answers</summary>

1. **b** — Models have a fixed context window. Large files can use thousands of tokens, leaving no room for the prompt and response.
2. **c** — Top-k retrieval finds the k chunks most similar to the query using embedding similarity.
3. **b** — Overlap ensures that code at chunk boundaries isn't lost — it appears in both the end of one chunk and the start of the next.

</details>

---

## Capstone Progress 🏗️

Your Issue Reviewer can now handle large repositories!

| Chapter | Feature | Status |
|---------|---------|--------|
| 0 | Basic SDK setup & issue summarization | ✅ |
| 1 | Structured JSON output with Pydantic validation | ✅ |
| 2 | Reliable classification with prompt engineering | ✅ |
| 3 | Tool calling for file access | ✅ |
| 4 | Streaming UX & agent loop awareness | ✅ |
| 5 | Concept extraction & mentoring advice | ✅ |
| **6** | **RAG for large repositories** | **✅ New!** |
| 7 | Safety & guardrails | ⬜ |
| 8 | Evaluation & testing | ⬜ |
| 9 | Production hardening & GitHub integration | ⬜ |

> 📝 **Note**: This chapter is an **optional advanced track** in the capstone. If RAG isn't needed for your use case (small repos), you can continue with the `get_file_contents` tool from Chapter 3.

## Next Step

In [Chapter 7 — Safety & Guardrails](../07-safety-guardrails/README.md), you'll learn how to protect your agent from prompt injection, unsafe file access, and other adversarial inputs.

---

## Additional Resources

- [RAG (Retrieval-Augmented Generation) explained](https://research.ibm.com/blog/retrieval-augmented-generation-RAG)
- [Text embeddings guide](https://platform.openai.com/docs/guides/embeddings)

### 📖 Extra Reading: RAG Architecture Patterns

For production RAG systems, consider these patterns:

- **When RAG is necessary**: Repos > 100 files, files > 1,000 lines, context window approaching limits
- **Latency trade-offs**: Pre-indexing is slow but search is fast; full-file reads are fast but may exceed context
- **Embedding refresh**: Re-index when files change (git hooks, CI pipeline)
- **Hybrid search**: Combine keyword matching with semantic embeddings for better results
- **Chunking by AST**: Use the Abstract Syntax Tree to split at function/class boundaries instead of line counts
