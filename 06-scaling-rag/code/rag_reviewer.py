"""
Chapter 6 — Scaling with Retrieval (RAG): Starter Code
GitHub Copilot SDK for Beginners

Replace full-file injection with RAG-based retrieval for large repositories.
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
    """Split content into chunks of approximately chunk_size lines with overlap.
    
    Each chunk should be a dict with:
      - "content": the text of the chunk
      - "start_line": 1-based start line number
      - "end_line": 1-based end line number
    """
    # TODO 1: Split content by newlines and create overlapping chunks.
    #   Loop from 0 to len(lines) stepping by (chunk_size - overlap).
    #   For each step, extract chunk_size lines and record start/end.
    return []


# --- Embeddings & Similarity ---

def simple_embed(text: str) -> Counter:
    """Create a bag-of-words embedding from text."""
    # TODO 2: Extract lowercase identifiers using regex
    #   Pattern: r'\b[a-z_][a-z0-9_]*\b'
    #   Return a Counter of the words
    return Counter()


def similarity(embed_a: Counter, embed_b: Counter) -> float:
    """Compute cosine similarity between two bag-of-words embeddings."""
    # TODO 3: Compute cosine similarity:
    #   1. Find common keys
    #   2. Compute dot product of common values
    #   3. Compute magnitudes
    #   4. Return dot_product / (mag_a * mag_b)
    return 0.0


# --- Chunk Index ---

class ChunkIndex:
    """In-memory index of file chunks for retrieval."""

    def __init__(self):
        self.chunks: list[dict] = []

    def add_file(self, file_path: str, content: str):
        """Index a file by splitting it into chunks."""
        # TODO 4: Chunk the content and add file_path to each chunk.
        #   Append all chunks to self.chunks.
        pass

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Retrieve the k most relevant chunks for a query."""
        # TODO 5: Embed the query, score all chunks by similarity,
        #   sort by score descending, return top k.
        return []


# --- Global index ---
index = ChunkIndex()


# --- Tool Definition ---

class SearchParams(BaseModel):
    query: str = Field(description="Search query to find relevant code")


@define_tool(description="Search the repository for code relevant to a query. "
             "Returns the most relevant code chunks.")
async def search_code(params: SearchParams) -> str:
    """Search indexed code chunks for relevant content."""
    results = index.search(params.query, k=3)
    if not results:
        return "No relevant code found."

    output = []
    for r in results:
        output.append(
            f"--- {r['file_path']} (lines {r['start_line']}-{r['end_line']}) ---\n"
            f"{r['content']}"
        )
    return "\n\n".join(output)


# --- Schema ---

class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str
    chunks_used: int


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
}"""


SAMPLE_ISSUE = """
Title: Fix token expiry validation in auth system

The validate_token() function doesn't check the 'exp' claim.
Expired JWT tokens are accepted by the login handler.
"""


async def main():
    # Index repository files
    repo_root = os.environ.get("REPO_PATH", ".")
    print("📂 Indexing repository...\n")

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("node_modules", "__pycache__", "venv")]
        for f in files:
            if f.endswith((".py", ".js", ".ts")):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, repo_root)
                try:
                    with open(path, "r") as fh:
                        index.add_file(rel_path, fh.read())
                except Exception:
                    pass

    print(f"✅ Indexed {len(index.chunks)} chunks\n")

    # Review the issue
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
        "tools": [search_code],
    })

    print("📋 Sending issue for review...\n")
    response = await session.send_and_wait({"prompt": SAMPLE_ISSUE})

    # TODO 6: Parse the response and display the results
    print(response.data.content)

    await client.stop()


asyncio.run(main())
