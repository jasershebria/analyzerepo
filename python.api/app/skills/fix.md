---
name: fix
description: Find and fix a bug or issue in the codebase
---
Find and fix the described bug or issue.

Steps:
1. Use rag_search and grep to locate the relevant code
2. Read the affected files fully with file_read
3. Use todo_write to outline the fix plan before making changes
4. Apply the fix with file_edit
5. Verify the fix makes sense by re-reading the changed code

Be surgical — fix only what is broken. Do not refactor unrelated code.
Explain what caused the bug and what the fix does.
