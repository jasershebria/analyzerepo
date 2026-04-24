---
name: test
description: Write comprehensive tests for the specified code
---
Write thorough tests for the relevant code in this repository.

Steps:
1. Use rag_search to find the code to test
2. Read it fully with file_read to understand inputs, outputs, and edge cases
3. Use todo_write to plan: unit tests, integration tests, edge cases
4. Write tests following the existing test patterns in the project (run glob to find test files first)
5. Ensure tests cover: happy path, error cases, boundary conditions

Write tests that will actually catch regressions, not just pass trivially.
