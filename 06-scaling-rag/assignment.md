# Assignment — Scaling with Retrieval (RAG)

## Objectives

Replace full-file injection with retrieval-based context to handle large repositories efficiently.

> 📝 This is an **optional advanced track**. If your repository is small, you can skip this and continue using `get_file_contents` from Chapter 3.

## What You'll Build

A RAG-enhanced Issue Reviewer that:

1. **Indexes** repository files into chunks
2. **Searches** for the most relevant chunks when analyzing an issue
3. **Injects** only the top results into the agent's context
4. **Compares** token usage between full-file and RAG approaches

## Instructions

### Step 1 — Implement Chunking

Open `code/rag_reviewer.py`. Complete the `chunk_by_lines` function that splits file content into overlapping chunks.

### Step 2 — Build the Similarity Function

Complete the `simple_embed` and `similarity` functions for keyword-based similarity scoring.

### Step 3 — Create the ChunkIndex

Complete the `ChunkIndex` class that stores chunks and retrieves the top-k most relevant results for a query.

### Step 4 — Connect to the Agent

Replace the `get_file_contents` tool with a `search_code` tool that uses the `ChunkIndex` to return relevant chunks instead of full files.

### Step 5 — Compare Approaches

Run the same issue with both full-file and RAG approaches. Compare token usage (character count) and response quality.

## Stretch Goals

- 🌟 Add function/class name extraction to chunk metadata
- 🌟 Try different chunk sizes (20, 50, 100 lines) and compare retrieval quality
- 🌟 Index an actual open-source repository and run a real issue through the system
- 🌟 Implement a `list_files` tool alongside `search_code` so the agent can discover the repo structure

## Rubric

| Criteria | Meets Expectations |
|----------|-------------------|
| Chunking works | Files are split into overlapping chunks |
| Search returns results | `search_code` returns the top-k most relevant chunks |
| Reduced context | RAG approach uses significantly fewer tokens than full-file |
| Agent integration | The `search_code` tool works within the agent's tool loop |
| Comparison done | Student has compared full-file vs RAG with notes |
