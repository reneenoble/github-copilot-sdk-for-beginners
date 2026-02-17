"""
Chapter 6 — Scaling with Retrieval (RAG): Solution
GitHub Copilot SDK for Beginners

RAG-enhanced Issue Reviewer that indexes files into chunks and retrieves
only the most relevant context for analysis.
"""

import asyncio
import json
import os
import re
from collections import Counter
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
from typing import Literal


# --- Chunking ---

def chunk_by_lines(content: str, chunk_size: int = 50, overlap: int = 5) -> list[dict]:
    """Split content into overlapping chunks of approximately chunk_size lines."""
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


# --- Embeddings & Similarity ---

def simple_embed(text: str) -> Counter:
    """Create a bag-of-words embedding from text."""
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


# --- Chunk Index ---

class ChunkIndex:
    """In-memory index of file chunks for retrieval."""

    def __init__(self):
        self.chunks: list[dict] = []

    def add_file(self, file_path: str, content: str):
        """Index a file by splitting it into chunks."""
        file_chunks = chunk_by_lines(content)
        for chunk in file_chunks:
            chunk["file_path"] = file_path
            self.chunks.append(chunk)
        print(f"  📦 Indexed {file_path} ({len(file_chunks)} chunks)")

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve the k most relevant chunks for a query."""
        query_embed = simple_embed(query)
        scored = []
        for chunk in self.chunks:
            score = similarity(query_embed, simple_embed(chunk["content"]))
            scored.append({**chunk, "score": score})
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:k]


# --- Global index ---
index = ChunkIndex()


# --- Tool Definition ---

class SearchParams(BaseModel):
    query: str = Field(description="Search query to find relevant code")


@define_tool(description="Search the repository for code relevant to a query. "
             "Returns the most relevant code chunks, not full files.")
async def search_code(params: SearchParams) -> str:
    """Search indexed code chunks for relevant content."""
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

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.
"""


SAMPLE_ISSUE = """
Title: Fix token expiry validation in auth system

The validate_token() function doesn't check the 'exp' claim.
Expired JWT tokens are accepted by the login handler.
This is a security vulnerability affecting authentication.
"""


async def main():
    # Index repository files
    repo_root = os.environ.get("REPO_PATH", ".")
    print("📂 Indexing repository...\n")

    file_count = 0
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("node_modules", "__pycache__", "venv")]
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".md")):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, repo_root)
                try:
                    with open(path, "r") as fh:
                        content = fh.read()
                    index.add_file(rel_path, content)
                    file_count += 1
                except Exception:
                    pass

    print(f"\n✅ Indexed {file_count} files → {len(index.chunks)} chunks\n")

    # --- Review the issue ---
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
        "tools": [search_code],
        "streaming": True
    })

    session.on("tool.execution_start",
               lambda e: print(f"  🔍 Searching: {e.data.tool_name}"))
    session.on("tool.execution_complete",
               lambda e: print(f"  ✅ Search complete\n"))

    print("📋 Sending issue for review...\n")
    response = await session.send_and_wait({"prompt": SAMPLE_ISSUE})

    try:
        review = IssueReview.model_validate_json(response.data.content)
        print(f"\n{'═' * 50}")
        print(f"  📝 {review.summary}")
        print(f"  📊 Difficulty: {review.difficulty_score}/5 "
              f"({review.recommended_level})")
        print(f"  🧠 Concepts: {', '.join(review.concepts_required)}")
        print(f"  📦 Chunks used: {review.chunks_used}")
        print(f"  💡 Advice: {review.mentoring_advice}")
        print(f"{'═' * 50}")
    except Exception as e:
        print(f"  ⚠️ Parse error: {e}")
        print(f"  Raw: {response.data.content[:300]}")

    await client.stop()


asyncio.run(main())
