# GitHub Copilot SDK for Beginners: Build an AI GitHub Issue Reviewer

![Course banner showing a friendly robot reviewing GitHub issues](./images/repo-banner.png)

<!-- TODO: Add banner image to ./images/repo-banner.png — A wide (1280×640) branded illustration showing a friendly AI assistant robot reviewing GitHub issues on a screen, with the course title overlaid. Use a consistent illustration style (e.g., line art or watercolor) that will carry through all chapter images. -->

[![GitHub license](https://img.shields.io/github/license/microsoft/github-copilot-sdk-for-beginners)](LICENSE)
[![GitHub contributors](https://img.shields.io/github/contributors/microsoft/github-copilot-sdk-for-beginners)](https://github.com/microsoft/github-copilot-sdk-for-beginners/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/microsoft/github-copilot-sdk-for-beginners)](https://github.com/microsoft/github-copilot-sdk-for-beginners/issues)
[![GitHub stars](https://img.shields.io/github/stars/microsoft/github-copilot-sdk-for-beginners)](https://github.com/microsoft/github-copilot-sdk-for-beginners/stargazers)

🎯 [What You'll Learn](#-what-youll-learn) &ensp; ✅ [Prerequisites](#-prerequisites) &ensp; 📚 [Course Structure](#-course-structure) &ensp; 📋 [Glossary](./GLOSSARY.md)

> **✨ Learn to build intelligent, tool-using AI agents with the GitHub Copilot SDK by creating a production-ready GitHub Issue Reviewer.**

This hands-on course teaches you to build AI agents that can reason, plan, and take action. You'll work through 10 lessons, each adding a new capability to the capstone project — a GitHub Issue Reviewer that classifies issues, extracts concepts, and provides mentoring advice.

**No AI agent experience required.** If you know basic Python, you can learn this.

**Perfect for:** Developers who want to build AI-powered automation tools, not just use them.

## 🎯 What You'll Learn

## 🎯 What You'll Learn

Across 10 chapters, you'll incrementally build an **AI-powered GitHub Issue Reviewer** that:

- Reads GitHub issues via the API
- Analyzes referenced files from the repository
- Classifies difficulty (Junior → Senior+)
- Extracts required concepts and skills
- Provides mentoring advice tailored to skill level
- Streams progress updates to the terminal
- Posts structured results back to GitHub
- Includes evaluation, guardrails, and production hardening

![Diagram showing the capstone project architecture: GitHub Issue → Copilot SDK Agent → Classification, Advice, Labels → GitHub Comment](./images/capstone-architecture.png)

<!-- TODO: Add architecture diagram to ./images/capstone-architecture.png — A flow diagram showing: "GitHub Issue" → "Copilot SDK Agent" (with sub-steps: read issue, fetch files, classify, advise) → "Structured Output" → "GitHub Comment + Labels". Use clean boxes/arrows in brand colors. -->

## ✅ Prerequisites

- **Python 3.9+** installed
- **GitHub Copilot CLI** installed and authenticated ([Installation guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli))
- A **GitHub Copilot subscription** (free tier available)
- Basic familiarity with **Python** and **the command line**
- A **GitHub account**

## 📚 Course Structure

| Chapter | Title | What You'll Build |
|:-------:|-------|-------------------|
| 00 | 🚀 [Getting Started](./00-getting-started/README.md) | SDK setup & first agent |
| 01 | 📦 [Structured Output](./01-structured-output/README.md) | JSON schema validation |
| 02 | 🎯 [Prompt Engineering](./02-prompt-engineering/README.md) | Reliable classification |
| 03 | 🔧 [Tool Calling](./03-tool-calling/README.md) | File access capabilities |
| 04 | ⚡ [Agent Loop & Streaming](./04-agent-loop-streaming/README.md) | Responsive multi-step agent |
| 05 | 🧠 [Concepts & Mentoring](./05-concepts-mentoring/README.md) | Contextual mentoring advice |
| 06 | 📚 [Scaling with RAG](./06-scaling-rag/README.md) | Large repository handling |
| 07 | 🛡️ [Safety & Guardrails](./07-safety-guardrails/README.md) | Security hardening |
| 08 | 🧪 [Evaluation & Testing](./08-evaluation-testing/README.md) | Test harness for reliability |
| 09 | 🚢 [Production Hardening](./09-production-hardening/README.md) | Ship to production |

## 📖 How This Course Works

Each chapter follows the same pattern:

1. **Real-World Analogy**: Understand the concept through familiar comparisons
2. **Core Concepts**: Learn the essential knowledge
3. **Hands-On Demos**: Run actual code and see results
4. **Practice Assignment**: Build toward the capstone
5. **What's Next**: Preview of the following chapter

**Code examples are runnable.** Every code block in this course can be copied and executed.

## 🚀 Get Started

**[Start with Chapter 00 →](./00-getting-started/README.md)**

Fork this repo and complete each chapter at your own pace.

## 🏗️ How to Use This Repo

1. **Fork** this repository to your own GitHub account.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/github-copilot-sdk-for-beginners.git
   cd github-copilot-sdk-for-beginners
   ```
3. Work through each lesson **in order** — they build on each other.
4. Each chapter has a `code/` folder (starter code with TODOs) and a `solution/` folder (complete reference).
5. Complete the **assignment** at the end of each chapter to advance the capstone project.

## 🛠️ Quick Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the GitHub Copilot SDK
pip install github-copilot-sdk

# Verify the Copilot CLI
copilot --version
```

## 🙋 Getting Help

- 🐛 **Found a bug?** [Open an Issue](https://github.com/microsoft/github-copilot-sdk-for-beginners/issues)
- 🤝 **Want to contribute?** PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)
- 📚 **Need definitions?** Check the [Glossary](./GLOSSARY.md)
- 📖 **Official Docs:** [GitHub Copilot SDK Documentation](https://github.com/github/copilot-sdk)

## 👥 Meet the Team

<!-- TODO: Add team headshots to ./images/team/ — One image per team member (200×200 square, friendly professional headshot). Name files as firstname-lastname.png -->

*Coming soon*

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs and issues in lessons
- Suggesting new content
- Contributing translations
- Submitting pull requests

## 📚 Other Courses in the "For Beginners" Series

| Course | Link |
|--------|------|
| Generative AI for Beginners | [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) |
| ML for Beginners | [microsoft/ML-For-Beginners](https://github.com/microsoft/ML-For-Beginners) |
| Web Dev for Beginners | [microsoft/Web-Dev-For-Beginners](https://github.com/microsoft/Web-Dev-For-Beginners) |
| Data Science for Beginners | [microsoft/Data-Science-For-Beginners](https://github.com/microsoft/Data-Science-For-Beginners) |
| AI for Beginners | [microsoft/AI-For-Beginners](https://github.com/microsoft/AI-For-Beginners) |

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
