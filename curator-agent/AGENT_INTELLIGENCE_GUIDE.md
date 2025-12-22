# Agent Intelligence Guide: Building Trust Through Transparency

## What We Learned

The curator agent demonstrated that AI agents can exhibit real intelligence when given:
1. **Rich context** (domain knowledge, examples, methodology)
2. **Clear goals** (what to accomplish, not how)
3. **Transparency mechanisms** (visibility into decisions)
4. **Human oversight** (approval before execution)

## Core Principles

### 1. Autonomous Intelligence, Not Automation

**Wrong Approach:**
```
User: "Extract ImuManager depends_on LinuxI2cDriver"
Agent: *extracts exactly that*
```

**Right Approach:**
```
User: "Build a dependency graph for F´ I2C subsystem"
Agent: *analyzes documentation*
Agent: *identifies 4 dependencies*
Agent: *validates each one*
Agent: "I found these dependencies. Should I store them?"
```

**Key Difference:**
- Automation: Do exactly what I say
- Intelligence: Figure out what needs to be done

### 2. Learning from Context

The agent becomes intelligent through **transfer learning**:

```python
task = """You are building a CubeSat dependency graph.

LEARN FROM THESE EXAMPLES:

Example 1:
  ImuManager depends_on LinuxI2cDriver
  Criticality: HIGH
  Reasoning: "IMU gets orientation via I2C. If I2C fails, satellite
  can't orient solar panels → power loss → mission failure"

Example 2:
  SensorCollector requires I2cBus
  Criticality: MEDIUM
  Reasoning: "Sensors use I2C but have backup polling.
  Degraded not catastrophic"

YOUR TASK:
- Analyze new documentation
- Find similar dependencies
- Apply the same reasoning methodology
- Discover dependencies we missed
"""
```

**What the Agent Learns:**
1. **Patterns**: What makes a dependency HIGH vs MEDIUM
2. **Reasoning Style**: How to assess mission impact
3. **Domain Knowledge**: CubeSat failure modes
4. **Methodology**: Look for cascade failures

### 3. Transparency: Show Your Work

Every agent action must be **visible and traceable**:

#### What We Built:
1. **Console Output**: Real-time progress
   ```
   [CURATOR] Thinking...
   [CURATOR] Planning to call 4 sub-agent(s):
     -> validator_agent (x4)
   [TOOLS] Executing sub-agent tool calls...
   ```

2. **Checkpoint Database**: Full conversation history
   ```bash
   python view_session.py demo-learning
   # Shows every decision, tool call, result
   ```

3. **Monitoring Tools**: See what's in the graph
   ```bash
   python quick_monitor.py
   # Shows stored dependencies in real-time
   ```

4. **Logs**: Debug file with reasoning
   ```python
   logging.info("[CURATOR] Found 4 dependencies")
   logging.info("[CURATOR] Assessing criticality...")
   ```

#### Why This Matters:
- **Trust**: You can see what the agent is thinking
- **Accountability**: Every decision is recorded
- **Learning**: Review sessions to improve prompts
- **Debugging**: Trace errors to specific decisions

### 4. Human-in-the-Loop: Two Levels

#### Level 1: Data-Level Approval (Current)
- Agent works autonomously
- Gates on HIGH criticality storage
- Human approves/rejects based on impact

```
Agent: "I want to store this HIGH criticality dependency"
Human: *reviews* "Yes, that's mission-critical"
Agent: *stores*
```

#### Level 2: Action-Level Approval (Proposed)
- Agent plans autonomously
- Human approves each execution step
- Shows reasoning before acting

```
Agent: "I want to call extractor_agent to read fprime_i2c_driver.md"
Agent: "This will help me find I2C dependencies"
Human: "Approved"
Agent: *reads and analyzes*
Agent: "Found 4 dependencies. Should I validate them?"
Human: "Approved"
```

## How to Create Intelligence

### Recipe for Smart Agents

**1. Give Domain Context**
```python
system_message = """
DOMAIN: CubeSat mission safety
PROBLEM: Hidden dependencies cause cascade failures
EXAMPLE: FalconSat-2 failed because power→I2C dependency wasn't documented
IMPACT: $2M satellite loss, 3 years of work gone
"""
```

**2. Provide Examples (Few-Shot Learning)**
```python
"""
LEARN FROM STUDENTS' WORK:

Good Example:
  Source: ImuManager
  Target: LinuxI2cDriver
  Type: depends_on
  Criticality: HIGH
  Reasoning: [detailed explanation]

Bad Example (missed):
  TimeManager needs GPS
  Should be HIGH (time sync critical) but students marked MEDIUM
  Learn from this oversight
"""
```

**3. Set Clear Goals, Not Steps**
```python
# Bad: Prescriptive
"Extract dependencies from file X, validate with Y, store in Z"

# Good: Goal-oriented
"Build a complete dependency graph for the I2C subsystem.
Find dependencies students might have missed.
Suggest improvements to the extraction methodology."
```

**4. Enable Exploration**
```python
"""
You have access to:
- extractor_agent: Read and analyze documentation
- validator_agent: Check for duplicates/conflicts
- storage_agent: Store in knowledge graph

Decide which to use and when. Explain your reasoning.
"""
```

### What Makes an Agent "Intelligent"

✓ **Understands context** - Learns from examples
✓ **Makes decisions** - Chooses which tools to call
✓ **Explains reasoning** - Shows why it chose an action
✓ **Discovers insights** - Finds things humans missed
✓ **Improves methodology** - Suggests better approaches
✓ **Adapts to feedback** - Learns from approvals/rejections

## Implementation Patterns

### Pattern 1: Learning from Student Work

```python
def create_learning_task(student_examples, new_document):
    """
    Agent learns methodology from examples, applies to new data
    """
    return f"""
    STUDENT METHODOLOGY:
    {format_examples(student_examples)}

    YOUR TASK:
    1. Analyze their approach
    2. Apply to {new_document}
    3. Find what they missed
    4. Suggest improvements

    Show your reasoning at each step.
    """
```

**Result**: Agent transfers knowledge, doesn't just copy

### Pattern 2: Explain Before Execute

```python
def request_approval_with_reasoning(tool_name, args, reasoning):
    """
    Show what agent wants to do AND WHY
    """
    approval = interrupt({
        "tool": tool_name,
        "args": args,
        "reasoning": reasoning,  # ← KEY: Show the why
        "expected_outcome": "Find I2C dependencies",
        "risk": "None - read-only operation"
    })
    return approval == "approved"
```

**Result**: Human understands decision, can guide better

### Pattern 3: Iterative Refinement

```python
"""
After storing dependencies:
1. Show statistics (4 HIGH, 2 MEDIUM, 1 LOW found)
2. Compare to student work (found 2 they missed)
3. Suggest improvements:
   - "Consider tracking error recovery dependencies"
   - "Configuration dependencies seem underrepresented"
4. Ask: "Should I re-analyze with these insights?"
"""
```

**Result**: Agent gets smarter over time

## Monitoring and Tracing

### Essential Visibility Tools

**1. Real-Time Console Output**
```python
print("[CURATOR] Thinking...")
print("[CURATOR] Planning to call: extractor_agent")
print("[CURATOR] Reason: Need to read fprime I2C documentation")
```

**2. Structured Logging**
```python
logger.info("Agent decision", extra={
    "action": "call_tool",
    "tool": "extractor_agent",
    "reasoning": "...",
    "confidence": "high"
})
```

**3. Checkpoint Inspection**
```bash
# View full conversation
python view_session.py <thread-id>

# See all decisions
python simple_check.py
```

**4. Graph Monitoring**
```bash
# Watch dependencies being added
python quick_monitor.py watch

# Query by criticality
MATCH ()-[r:DEPENDS_ON {criticality: 'HIGH'}]->() RETURN r
```

### What to Track

✓ Tool calls (which, when, why)
✓ Reasoning (what led to each decision)
✓ Results (what each tool returned)
✓ Approvals (human decisions and timing)
✓ Discoveries (new insights found)
✓ Errors (what failed and why)
✓ Performance (time per operation)

## Trust Through Transparency

### The Transparency Stack

```
┌─────────────────────────────────────┐
│  USER: Sees decisions in real-time │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  CONSOLE: Live progress updates     │
│  [CURATOR] Thinking...              │
│  [CURATOR] Planning to call...      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  CHECKPOINTS: Full conversation     │
│  Every message, decision, result    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  LOGS: Detailed reasoning           │
│  Why each decision was made         │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  DATABASE: Final stored results     │
│  Neo4j graph with full provenance   │
└─────────────────────────────────────┘
```

### Building Trust Incrementally

**Phase 1: Supervised Mode**
- Agent asks approval for EVERY action
- Human sees all reasoning
- Builds confidence in agent's judgment

**Phase 2: Semi-Autonomous**
- Agent handles LOW/MEDIUM automatically
- Human approves HIGH criticality only
- Faster workflow, maintained safety

**Phase 3: Autonomous with Review**
- Agent works independently
- Human reviews results afterward
- Can rollback if needed

**Phase 4: Full Autonomy**
- Agent handles everything
- Human spot-checks periodically
- Intervention only on errors

## Key Takeaways

### For Building Intelligent Agents:

1. **Context is Intelligence**
   - Rich domain knowledge → Better decisions
   - Good examples → Better methodology
   - Clear goals → Better outcomes

2. **Transparency Enables Trust**
   - Show all decisions → Human can verify
   - Explain reasoning → Human understands why
   - Record everything → Audit trail exists

3. **HITL is About Control, Not Micromanagement**
   - Let agent plan and reason
   - Gate on execution, not thinking
   - Approve based on impact, not detail

4. **Learning Compounds**
   - Each session improves prompts
   - Approvals teach preferences
   - Discoveries enrich context

### For Users:

1. **Give Context, Not Commands**
   ```
   Bad:  "Extract this exact dependency"
   Good: "Here's what good extraction looks like. Find more."
   ```

2. **Ask "Why?" Not Just "What?"**
   ```
   Bad:  "Did it work?"
   Good: "Why did it choose that criticality level?"
   ```

3. **Review Sessions, Improve Prompts**
   ```bash
   python view_session.py last-run
   # Find where reasoning was weak
   # Add examples to improve next time
   ```

4. **Trust, But Verify**
   ```bash
   python quick_monitor.py
   # Spot-check stored dependencies
   # Look for patterns in what agent finds
   ```

## Conclusion

Intelligence in AI agents comes from:
- **Rich context** (domain knowledge + examples)
- **Autonomous decision-making** (let them think)
- **Transparent operation** (show all reasoning)
- **Human oversight** (approve before executing)

The curator agent demonstrated all four:
1. Learned from students' methodology
2. Autonomously chose to extract → validate → store
3. Showed every step: tool calls, reasoning, results
4. Would have requested approval before storage (hit API limit)

This is the model for trustworthy autonomous agents.
