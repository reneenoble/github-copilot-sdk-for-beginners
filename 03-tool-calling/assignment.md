# Assignment: Give the Agent Eyes

## Objectives

After completing this assignment, you will have:
- [ ] A `get_file_contents` tool defined with `@define_tool`
- [ ] The tool integrated into the Issue Reviewer session
- [ ] Tool call logging to see when files are fetched
- [ ] A `files_analyzed` field in the structured output

## Instructions

### Step 1: Define the Tool

Create a `get_file_contents` tool that accepts a `file_path` parameter and reads that file from a local repository directory. Include path traversal protection.

### Step 2: Add the Tool to Your Session

Pass the tool in the `tools` list when creating a session. Update your system prompt to instruct the model to use the tool when issues reference files.

### Step 3: Add Logging

Use event listeners to print when tools are called and when they complete. This helps you understand the model's reasoning process.

### Step 4: Test with File References

Create a test issue that references specific files. Run your reviewer against a local repository to verify it reads the files.

## Stretch Goals (Optional)
- 🌟 Add a second tool: `list_directory(path)` that lists files in a directory
- 🌟 Add logging that shows how long each tool call takes
- 🌟 Intentionally restrict file access (e.g., block `.env` files) and verify the tool refuses

## Rubric

| Criteria | Complete |
|----------|----------|
| `get_file_contents` tool defined with Pydantic schema | ✅ |
| Tool passed to session via `tools` config | ✅ |
| Path traversal protection implemented | ✅ |
| Tool call events logged to terminal | ✅ |
| `files_analyzed` included in output schema | ⭐ (bonus) |
