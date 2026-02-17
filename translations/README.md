# Translations

We welcome community translations of this course! If you'd like to contribute
a translation, please follow the guidelines below.

## Available Translations

| Language | Contributors | Link |
|---|---|---|
| English (original) | Microsoft | [English](../README.md) |

> **Want to add your language?** Open a PR following the contribution steps
> below and we'll add it to this table!

## How to Contribute a Translation

1. **Open an issue** using the
   [Translation Request](../.github/ISSUE_TEMPLATE/translation.md) template
   to let others know you're working on a specific language.

2. **Fork** the repository and create a branch named
   `translations/<language-code>` (e.g. `translations/es` for Spanish).

3. **Create a folder** inside `translations/` using the two-letter
   [ISO 639-1 code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
   for your language (e.g. `translations/es/`).

4. **Translate the lesson content** — each chapter's `README.md` and
   `assignment.md`. Keep the same folder structure:

   ```
   translations/es/
   ├── README.md          ← translated top-level README
   ├── 00-course-setup/
   │   ├── README.md
   │   └── assignment.md
   ├── 01-intro-copilot-sdk/
   │   ├── README.md
   │   └── assignment.md
   ...
   ```

5. **Do NOT translate** code files (`code/` and `solution/` folders), image
   filenames, or YAML front-matter keys. Comments inside code may be
   translated if helpful.

6. **Submit a PR** and tag it with the `translation` label.

## Translation Guidelines

- Keep technical terms (SDK, API, JSON, Pydantic, etc.) in English.
- Translate UI text, explanations, and instructions.
- Preserve all Markdown formatting — headings, tables, code fences, links.
- Keep image references pointing to the original English `images/` paths
  (unless you are also providing localized screenshots).
- Add a note at the top of each translated file:
  ```
  > 🌍 This is a community translation. For the original English version,
  > see [English](../../README.md).
  ```

## Review Process

Translation PRs are reviewed by maintainers and, when possible, native
speakers from the community. We may request changes for accuracy or
consistency before merging.

Thank you for helping make this course accessible to more developers! 🌐
