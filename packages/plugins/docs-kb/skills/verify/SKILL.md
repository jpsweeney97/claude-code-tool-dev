---
name: verify
description: Verify API usage against documentation before writing code
---

# docs-kb:verify

Verify API usage against documentation before writing code.

## When to Use

- Before writing code that uses libraries in docs-kb
- When unsure about API signatures, parameters, or patterns
- When the user says "verify this" or "check the docs"

## Step 1: Identify What to Verify

Analyze the current task and extract specific items:

**For code generation:**
- Imports or libraries mentioned
- Specific classes, functions, or methods
- Configuration patterns

**Extraction examples:**

| Task | Extract |
|------|---------|
| "Create a LangChain agent with tools" | `AgentExecutor`, `create_tool_calling_agent`, `Tool` |
| "Fix the VS Code extension sidebar" | `TreeDataProvider`, `TreeItem` |
| "Add FastAPI auth middleware" | `Depends`, `HTTPBearer`, `Security` |

## Step 2: Discover Available Sources

Call `list_sources` with `include_patterns: true` to see what documentation is available and which sources are relevant to the current task.

## Step 3: Query Documentation

For each concept to verify, call `ask` with:
- `question`: Specific query (e.g., "AgentExecutor constructor parameters and usage")
- `source`: The relevant source ID
- `context_mode`: "page" for thorough verification
- `limit`: 3

## Step 4: Synthesize Results

Do NOT paste entire responses. Extract and summarize:

**Required:**
- Function/method signatures with types
- Required parameters
- Return types
- One minimal working example

**Verification summary format:**
```
### Verified: AgentExecutor (langchain)

**Signature:**
AgentExecutor(agent, tools, memory=None, verbose=False, ...)

**Required:**
- agent: BaseAgent
- tools: List[Tool]

**Returns:** AgentExecutor instance

**Key pattern:**
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "query"})

**Gotchas:**
- tools must match between agent and executor
- use invoke(), not run() (deprecated)
```

Aim for 200-400 tokens per verified API.

## Step 5: Proceed with Coding

Apply verified knowledge to the task. Reference documentation if the user needs sources.

## Handling Multiple Sources

When patterns match multiple sources:
1. Check task context (existing imports, dependencies)
2. Ask if ambiguous
3. Query most likely first

## When Documentation Is Insufficient

1. **No results:** Check if source is ingested. Suggest WebSearch or official docs.
2. **Outdated:** Note discrepancy, suggest official URL, proceed with caution.
3. **Partial:** Use what's available, note gaps.

Be transparent about limitations rather than guessing.
