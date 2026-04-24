---
name: review
description: Thorough code review with actionable suggestions
---
Perform a thorough code review of the relevant files in this repository.

- Use rag_search to find the files most relevant to the review
- Read each file fully with file_read
- Check for: bugs, security issues, performance problems, code smells, missing error handling
- Reference specific file paths and line numbers
- Provide actionable, prioritized suggestions

Be concise and developer-focused. Group findings by severity: Critical, Warning, Suggestion.
