# ACTION-LEVEL HITL: Autonomous Planning with Execution Approval

## Goal
- Agent autonomously decides HOW to accomplish a task
- Human approves each ACTION before execution
- Criticality is just metadata, not a gate

## Architecture

### Current Flow
```
User: "Extract dependency X"
  → Agent: calls extractor
  → Agent: calls validator
  → Agent: calls storage (if HIGH, wait for approval)
  → Done
```

### Desired Flow
```
User: "Build dependency graph for F´ I2C"
  → Agent: Plans approach
  → Agent: "Should I read fprime_i2c_driver_full.md?" → WAIT
  → User: Approve
  → Agent: Reads file
  → Agent: "Should I extract 8 dependencies?" → WAIT
  → User: Approve
  → Agent: Extracts
  → Agent: "Should I store them?" → WAIT
  → User: Approve
  → Done
```

## Implementation Strategy

### Option 1: Tool-Level Approval

Modify `run_tools_with_gate()` to ask before executing ANY tool:

```python
def run_tools_with_gate(state: CuratorState):
    last_message = state["messages"][-1]
    if not (isinstance(last_message, AIMessage) and last_message.tool_calls):
        return {}

    tool_messages: list[ToolMessage] = []
    deferred_tools: list[dict[str, Any]] = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool_call_id = tool_call.get("id")
        args = tool_call.get("args") or {}

        # DEFER EVERY TOOL CALL for approval
        print(f"[HITL] Tool execution requested: {tool_name}")
        deferred_tools.append({
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "args": args
        })
        tool_messages.append(
            ToolMessage(
                content=f"DEFERRED: Waiting for approval to execute {tool_name}",
                tool_call_id=tool_call_id,
            )
        )

    return {
        "messages": tool_messages,
        "deferred_tools": deferred_tools  # NEW state field
    }
```

Then in approval node:
```python
def request_tool_approval(state: CuratorState):
    deferred = state.get("deferred_tools") or []
    if not deferred:
        return {"tool_approval": None}

    # Get first pending tool
    pending = deferred[0]
    tool_name = pending.get("tool_name")
    args = pending.get("args")

    # Show what the tool will do
    task = args.get("task", "")

    approval = interrupt({
        "type": "tool_execution_approval",
        "tool": tool_name,
        "task": task,
        "message": f"Agent wants to execute {tool_name}. Approve?"
    })

    return {
        "tool_approval": approval,
        "approved_tool": pending if approval == "approved" else None
    }
```

### Option 2: Plan-Then-Execute Pattern

Better approach - agent creates a plan first, shows it to you, then executes:

```python
# Add a new sub-agent: planner_agent
@tool("planner_agent")
def call_planner_agent(goal: str) -> str:
    """
    Call the planner to break down a high-level goal into steps.

    Args:
        goal: The high-level objective (e.g., "Build dependency graph for F´ I2C")

    Returns:
        A detailed execution plan with steps
    """
    planner = create_planner_agent()
    result = planner.invoke({"messages": [{"role": "user", "content": goal}]})
    return result['messages'][-1].content
```

Then modify the workflow:
```
1. User gives goal
2. Agent calls planner_agent to create plan
3. Agent presents plan to user → INTERRUPT
4. User approves plan
5. Agent executes plan step-by-step
6. After each step, agent asks to continue → INTERRUPT
7. User approves next step
8. Repeat until done
```

### Option 3: Interactive Mode (Simplest)

Add a config flag for "interactive mode":

```python
def create_curator(interactive_mode: bool = False):
    """
    Args:
        interactive_mode: If True, ask for approval before each tool execution
    """

    def run_tools_with_gate(state: CuratorState):
        # ... tool execution logic

        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")

            if interactive_mode:
                # Defer ALL tools for approval
                deferred_tools.append(tool_call)
            else:
                # Current behavior: only defer HIGH storage
                if _is_high_criticality_storage_call(tool_call):
                    deferred_storage.append(tool_call)
                else:
                    # Execute immediately
                    result = execute_tool(tool_call)
```

## Recommended Approach

**Option 2: Plan-Then-Execute** is best because:

1. Agent autonomously plans (shows intelligence)
2. You see the full plan before execution (transparency)
3. You approve step-by-step (control)
4. Aligns with your goal: "Let it decide HOW, I approve execution"

## Example Implementation

```python
# New workflow:
# user → agent → planner → [show plan] → INTERRUPT
#     ↓
# approve → executor → [execute step 1] → INTERRUPT
#     ↓
# approve → [execute step 2] → INTERRUPT
#     ↓
# approve → done
```

## Current Status

**What's Implemented**: Data-level approval (optional HIGH criticality gate)

**What's Demonstrated**: The `demo_learning.py` script shows autonomous intelligence where the agent:

- Learns from examples autonomously
- Decides which tools to call (extractor, validator, storage)
- Makes intelligent decisions without step-by-step instructions
- Would request approval before storage (hit API limit during demo)

**Next Evolution**: Implementing Option 2 (Plan-Then-Execute) or Option 3 (Interactive Mode) would enable full action-level approval where the agent shows you its plan and requests approval before executing each action.

The key insight: Agent should plan autonomously but execute with approval. This demonstrates real intelligence while maintaining human control.
