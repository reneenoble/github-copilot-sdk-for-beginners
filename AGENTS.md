# Coding Agent Instructions

This repository is a beginner-friendly course teaching the GitHub Copilot SDK. It is structured as a series of progressive chapters.

## Repository Structure

```
README.md                          # Course landing page
GLOSSARY.md                        # Term definitions
for_beginners_style.md             # Style guide for "For Beginners" courses
00-getting-started/                # Chapter 00 — SDK setup, first agent
01-structured-output/              # Chapter 01 — JSON schemas, Pydantic
02-prompt-engineering/             # Chapter 02 — Rubrics, few-shot examples
03-tool-calling/                   # Chapter 03 — @define_tool, file reading
04-agent-loop-streaming/           # Chapter 04 — Agent loop, streaming events
05-safety-guardrails/              # Chapter 05 — Prompt injection defense, hooks
06-shipping-to-production/         # Chapter 06 — GitHub API, logging, retries
appendices/scaling-rag/            # Appendix — RAG for large repos
```

Each chapter folder contains:
- `README.md` — the lesson content
- `assignment.md` — the hands-on exercise
- `code/` — starter template (students fill in TODOs)
- `solution/` — completed reference implementation

## Conventions

- **Language**: All code is Python 3.11+, using `asyncio` and `await`
- **Dependencies**: `github-copilot-sdk>=0.3.0`, `pydantic`, `httpx`, `numpy` (appendix only)
- **Style guide**: See `for_beginners_style.md` for the required chapter structure
- **Tone**: Friendly, encouraging, jargon-explained. Target audience is developers who know Python basics but are new to AI agents.

## Chapter Structure Pattern

Every chapter README follows this pattern:
1. Banner image + intro quote
2. Learning Objectives
3. Real-World Analogy
4. Core Concepts with code examples
5. Try It Yourself (hands-on exercise)
6. Common Mistakes & Troubleshooting (in `<details>` block)
7. Knowledge Check (multiple choice, answers marked with ✅)
8. Summary with Key Takeaways
9. Capstone Progress tracker
10. What's Next preview
11. Additional Resources with Official Docs callout
12. Navigation links (← previous | next →)

## When Making Changes

- Keep the progressive capstone thread intact — each chapter builds on the previous one
- Preserve the consistent section structure across all chapters
- Use the Glossary for new terms (link with `> 📚 **Glossary**: ...`)
- Add `<!-- TODO: ... -->` comments for images/GIFs that need to be created
- Test code examples work with the Copilot SDK before committing
- Assignment rubrics should have measurable, specific criteria
