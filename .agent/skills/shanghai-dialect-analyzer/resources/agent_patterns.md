# Agent Skills and Iterative Workflows

## What are Agent Skills?

Agent Skills extend the capabilities of the AI assistant by packaging domain-specific knowledge, workflows, and scripts. The AI assistant can call these skills when needed.

A skill is defined in a `SKILL.md` file and can include:
1.  **Custom Commands**: Reusable workflows triggered by symbols like `/` in the assistant's input.
2.  **Hooks**: Scripts that run before or after the assistant's operations.
3.  **Domain Knowledge**: Specific task instructions that the assistant can pull as needed.

Unlike global rules, skills are dynamically loaded by the assistant when it judges them relevant. This keeps the context window clean while allowing for specialized capabilities.

## The "Grind" Pattern (Iterative Task Loop)

A powerful pattern is to create continuous-running agents that iterate until a goal is reached (e.g., all tests pass, UI matches design).

### Implementation with Hooks

Configure a hook in `.cursor/hooks.json`:
```json
{
  "version": 1,
  "hooks": {
    "stop": [{ "command": "bun run .agent/skills/shanghai-dialect-analyzer/scripts/grind.ts" }]
  }
}
```

### Hook Script Example (`grind.ts`)

The hook script receives context from `stdin` and can return a `followup_message` to continue the loop.

```typescript
import { readFileSync, existsSync } from "fs";

interface StopHookInput {
  conversation_id: string;
  status: "completed" | "aborted" | "error";
  loop_count: number;
}

const input: StopHookInput = await Bun.stdin.json();

const MAX_ITERATIONS = 5;

// If the task failed or limit reached, stop.
if (input.status !== "completed" || input.loop_count >= MAX_ITERATIONS) {
  console.log(JSON.stringify({}));
  process.exit(0);
}

// Check for a completion marker in a scratchpad file.
const scratchpad = existsSync(".cursor/scratchpad.md")
  ? readFileSync(".cursor/scratchpad.md", "utf-8")
  : "";

if (scratchpad.includes("DONE")) {
  console.log(JSON.stringify({}));
} else {
  // Otherwise, request a follow-up iteration.
  console.log(JSON.stringify({
    followup_message: `[Iteration ${input.loop_count + 1}/${MAX_ITERATIONS}] Continuing work. Please mark DONE in .cursor/scratchpad.md when finished.`
  }));
}
```

### Use Cases
-   Running (and fixing) until all tests pass.
-   Iterating on UI until it matches a design.
-   Any goal-oriented task where success can be verified programmatically or via a state file.
