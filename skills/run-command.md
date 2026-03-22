# run-command

Safely execute terminal commands and explain the results. Use when the user wants to run shell commands, check system status, or perform file operations.

## Instructions

When the user wants to run a terminal command:

1. **Understand the request** — Identify what command(s) the user wants to run. If unclear, ask for clarification.

2. **Safety check** — Before running potentially destructive commands (rm -rf, format, delete), confirm with the user:
   - "This will permanently delete files. Are you sure?"
   - Never run commands that could harm the system without explicit confirmation.

3. **Execute the command** — Use the terminal_server MCP tool to run the command.

4. **Explain the output** — Present the results in a clear, human-readable way:
   - For file listings: summarize what's there
   - For errors: explain what went wrong and suggest fixes
   - For success: confirm what was accomplished

5. **Suggest next steps** — If relevant, suggest follow-up commands the user might want to run.
