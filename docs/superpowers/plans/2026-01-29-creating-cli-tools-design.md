## Design Context: creating-cli-tools

**Type:** Process/workflow
**Risk:** Medium (writes files, creates executables)

### Problem Statement
> Creating CLI tools involves trial and error because vague ideas don't translate easily to concrete designs. Users have a rough sense of what they want but not how to get there, leading to iteration that could be avoided with upfront brainstorming.

### Success Criteria
> - Brainstorming methodology (one question at a time) leads to clear design before any code is written
> - Output is a ready-to-use CLI tool that can be invoked by name alone (like `tree`)
> - Tool follows Python conventions: full type hints, Ruff formatting, Google docstrings
> - Simple tools use PEP 723 inline metadata; complex tools use `uv tool install`

### Compliance Risks
- Claude skipping brainstorming to write a quick script directly (main risk)
- Mitigation: "YOU MUST" language, convergence tracking, rationalization table

### Rejected Approaches
- Language-agnostic skill: rejected because user specifically uses Python/click with UV
- Separate skill for simple vs complex tools: rejected because one skill with decision point is simpler
- Design document output (like brainstorming-skills): rejected because user wants ready-to-use tools, not design artifacts

### Design Decisions
- **PEP 723 with UV:** Enables single-file scripts with dependencies, reducing need for package structure
- **Shebang `#!/usr/bin/env -S uv run --script`:** The `--script` flag prevents recursion when invoked via `uv run`
- **No `.py` extension:** Allows invocation by name alone without specifying interpreter
- **`uv tool install` for complex tools:** Provides same UX (run by name) while supporting package structure
- **Paths hardcoded:** `/Users/jp/dotfiles/bin/.local/bin/` and `/Users/jp/Projects/tools/` — user-specific but consistent
