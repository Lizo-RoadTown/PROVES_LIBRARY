# HOW TO MONITOR THE CURATOR AGENT

## Quick Answer: Where Is Everything Stored?

### 1. **Conversation State** → `curator_checkpoints.db` (SQLite)
   - All conversation history
   - Agent decisions and tool calls
   - Approval requests and responses
   - **Location**: `c:\Users\LizO5\PROVES_LIBRARY\curator-agent\curator_checkpoints.db`

### 2. **Knowledge Graph** → Neo4j Database
   - Actual dependency data
   - Nodes (components, systems)
   - Relationships (depends_on, requires, etc.)
   - **Location**: Neo4j server (bolt://localhost:7687)

### 3. **Debug Logs** → Files (when logging enabled)
   - Agent thinking process
   - Tool execution details
   - Errors and warnings
   - **Location**: `curator_debug.log` (when enabled)

---

## IMMEDIATE VISIBILITY - Run These Commands

### See All Sessions
```bash
cd curator-agent
python view_session.py list
```

### See What Happened in Latest Session
```bash
python view_session.py
```

### See Specific Session
```bash
python view_session.py simple-test-1
```

### Watch What's in Neo4j (Real Dependencies)
First, install neo4j driver:
```bash
pip install neo4j
```

Then:
```bash
python quick_monitor.py          # One-time check
python quick_monitor.py watch 5  # Live updates every 5 seconds
```

---

## WHAT GETS STORED WHERE

### All Dependencies (Regardless of Criticality)

1. **Extractor finds them** → Stored in conversation
2. **Curator decides to store** → May request approval based on configuration
3. **After approval (if needed)** → Stored in Neo4j with criticality as metadata

**Note**: Criticality (HIGH/MEDIUM/LOW) is metadata that describes the dependency's importance, not a gate for whether it gets stored. All discovered dependencies should be extracted and stored in the knowledge graph.

### All Conversation Data
- Every message from you
- Every agent response
- Every tool call
- Every tool result
- Approval requests
- **ALL stored in**: `curator_checkpoints.db`

---

## ANSWER TO YOUR QUESTIONS

### "Was it recording all the other ones?"

**Check this way:**
```bash
# 1. Look at the conversation - did the extractor FIND other dependencies?
python view_session.py simple-test-1

# 2. Look at Neo4j - what was actually STORED?
python quick_monitor.py
```

The test script `test_simple_extraction.py` was FOCUSED - it only looked for ONE specific dependency. That's why you only saw one approval request.

If you want to see ALL dependencies extracted:
```bash
# Run this to extract EVERYTHING from a file
python run_with_approval.py 1  # Simple test (extracts all HIGH from I2C driver)
```

### "Everything is invisible to me"

**Fixed!** Now you can see:

1. **Checkpoint data**: `python view_session.py`
2. **Knowledge graph**: `python quick_monitor.py watch`
3. **Live execution**: Add logging (see below)

---

## ADD REAL-TIME LOGGING

Edit `src/curator/agent.py` and add at the top of `create_curator()`:

```python
import logging

# Add this at the very start of create_curator()
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('curator_debug.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("CURATOR AGENT STARTING")
logger.info("=" * 80)
```

Then run:
```bash
# In one terminal - run the agent
python run_with_approval.py

# In another terminal - watch the log
tail -f curator_debug.log
```

---

## TERMINAL COMMANDS TO WATCH EVERYTHING

### Watch Checkpoint Database Changes
```powershell
# PowerShell - watch file size changes
while($true) {
    Get-Item curator_checkpoints.db |
    Select-Object Name, Length, LastWriteTime
    Start-Sleep -Seconds 2
    Clear-Host
}
```

### Watch Neo4j (if running)
```bash
# Count dependencies in real-time
while true; do
    python -c "
from neo4j import GraphDatabase
import os
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as s:
    result = s.run('MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) as count')
    print(f'Dependencies: {result.single()[\"count\"]}')
driver.close()
"
    sleep 3
done
```

### Watch Debug Log
```bash
tail -f curator_debug.log
```

---

## FLAGS AND MECHANISMS FOR DECISION POINTS

### Current HITL (Human-in-the-Loop) System

HITL can operate at two levels:

1. **Action-Level Approval** (Recommended):
   - Agent decides WHAT to do autonomously
   - Agent requests approval before EXECUTING actions
   - You approve the agent's chosen approach
   - This tests autonomous intelligence

2. **Data-Level Approval** (Simple):
   - Agent can be configured to request approval for HIGH criticality storage
   - This is optional - criticality is primarily metadata
   - Most useful during initial testing

3. **Where to check for pending approvals**:
```bash
python -c "
import sys
sys.path.insert(0, '..')
from src.curator.agent import graph

config = {'configurable': {'thread_id': 'your-thread-id'}}
state = graph.get_state(config)

if '__interrupt__' in state.values:
    print('PENDING APPROVAL:', state.values['__interrupt__'])
else:
    print('No pending approvals')
"
```

### Add More Decision Points

Edit `src/curator/agent.py`:

```python
# In run_tools_with_gate(), add more checks:

if _is_high_criticality_storage_call(tool_call):
    # ... existing code ...
elif tool_name == "validator_agent" and "CONFLICT" in str(args):
    # New: Ask for approval on conflicts
    deferred_storage.append({"task": task, "reason": "CONFLICT_DETECTED"})
    tool_messages.append(ToolMessage(
        content="DEFERRED: Conflict detected, requesting approval",
        tool_call_id=tool_call_id
    ))
```

---

## SIMPLIFIED WORKFLOW

```
YOU ────► Task ────► Curator Agent
                         │
                         ├─► Extractor (finds dependencies)
                         │   └─► Results stored in checkpoint
                         │
                         ├─► Validator (checks for duplicates)
                         │   └─► Results stored in checkpoint
                         │
                         └─► Storage
                             ├─► HIGH? ──► WAIT for approval ──► You approve ──► Neo4j
                             └─► MEDIUM/LOW ──► Directly to Neo4j

MONITOR:
├─► Checkpoints: python view_session.py (full conversation history)
├─► Graph: python quick_monitor.py (stored dependencies)
└─► Console: Watch agent decisions in real-time
```

---

## NEXT STEPS

1. **Enable logging** (add logging to agent.py)
2. **Install neo4j**: `pip install neo4j`
3. **Run monitoring**: `python quick_monitor.py watch`
4. **Extract real data**: `python run_with_approval.py 1`

Then you'll have FULL VISIBILITY into:
- What the agent is thinking
- What tools it's calling
- What decisions it's making
- What data is being stored
- Where everything is located
