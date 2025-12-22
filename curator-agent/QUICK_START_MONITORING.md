# QUICK START: See What the Agent is Doing

## PROBLEM: "Everything is invisible to me"

## SOLUTION: 3-Step Visibility Setup

### STEP 1: Install Neo4j Driver (See the Knowledge Graph)

```bash
pip install neo4j
```

### STEP 2: Check What's Actually Stored

```bash
cd curator-agent
python -c "
from neo4j import GraphDatabase
import os

uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    # Count everything
    result = session.run('MATCH (n) RETURN count(n) as nodes')
    nodes = result.single()['nodes']

    result = session.run('MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) as deps')
    deps = result.single()['deps']

    print(f'Nodes in graph: {nodes}')
    print(f'Dependencies stored: {deps}')

    # Show all dependencies
    if deps > 0:
        print('\nAll dependencies:')
        result = session.run('''
            MATCH (a)-[r:DEPENDS_ON]->(b)
            RETURN a.name as source, b.name as target, r.criticality as crit
        ''')
        for record in result:
            print(f'  {record[\"source\"]} -> {record[\"target\"]} [{record[\"crit\"]}]')

driver.close()
"
```

### STEP 3: Add Logging to See Agent Thinking

Edit `src/curator/agent.py` - add this at line 93 (beginning of `create_curator()` function):

```python
def create_curator():
    # ADD THIS BLOCK FIRST:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(message)s',
        handlers=[
            logging.FileHandler('curator_debug.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('curator')
    logger.info("="*80)
    logger.info("CURATOR STARTING")
    logger.info("="*80)

    # ... rest of existing code
    print("Initializing Curator Agent...")
```

Then watch it in real-time:
```bash
# Terminal 1 - Run agent
python run_with_approval.py

# Terminal 2 - Watch log
tail -f curator_debug.log
```

---

## ANSWERING YOUR SPECIFIC QUESTIONS

### Q: "Did it record only HIGH, or all dependencies?"

**A**: The agent extracts and stores ALL dependencies it finds. Criticality (HIGH/MEDIUM/LOW) is just metadata that describes each dependency's importance - it's not a filter for what gets stored.

Check what was stored:

```bash
# What did the extractor FIND?
python view_session.py simple-test-1 | grep -i "dependency\|depends"

# What was STORED in Neo4j (with criticality levels)?
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as s:
    result = s.run('MATCH ()-[r:DEPENDS_ON]->() RETURN r.criticality, count(r) as count')
    for record in result:
        print(f'{record[\"criticality\"]}: {record[\"count\"]} dependencies')
"
```

### Q: "Is it replicating my trial work?"

**A**: Your trial manually extracted dependencies. The agent should do the same. To test:

```bash
# Run agent on same file you used manually
python run_with_approval.py 1  # Extract from fprime I2C driver

# Then check what it found vs what you found manually
```

### Q: "How can I see what scripts are being run?"

**A**: The agent doesn't run arbitrary scripts. It calls these three sub-agents:

1. **extractor_agent** - Reads docs, extracts dependencies
2. **validator_agent** - Checks for duplicates
3. **storage_agent** - Stores in Neo4j

Each sub-agent uses specific tools:
- `read_documentation_file()` - Reads files
- `check_if_dependency_exists()` - Queries Neo4j
- `store_dependency_relationship()` - Writes to Neo4j

See the actual code:
- Extractor: `src/curator/subagents/extractor.py`
- Validator: `src/curator/subagents/validator.py`
- Storage: `src/curator/subagents/storage.py`

---

## WHAT TO RUN RIGHT NOW

```bash
# 1. Install Neo4j driver
pip install neo4j

# 2. Check what's stored
python simple_check.py

# 3. Run a real extraction (not just a test)
python run_with_approval.py 1

# You'll see:
#  - Agent reads file
#  - Extracts dependencies
#  - Shows each HIGH dependency for approval
#  - Stores after you approve
```

---

## FILES TO WATCH

| **File** | **Contains** | **Command** |
|----------|-------------|-------------|
| `curator_checkpoints.db` | Conversation history | `python simple_check.py` |
| `curator_debug.log` | Agent thinking (if enabled) | `tail -f curator_debug.log` |
| Neo4j database | Actual stored dependencies | See Neo4j query above |

---

## THE KEY INSIGHT

The `test_simple_extraction.py` test was **intentionally narrow** - it only looked for ONE dependency to test HITL.

For a REAL extraction of ALL dependencies:

- Use `demo_learning.py` to see autonomous intelligence in action
- The agent learns from examples and finds dependencies on its own
- It decides WHAT to do autonomously
- It asks for approval before EXECUTING actions (not based on criticality)
- ALL dependencies are stored with their criticality as metadata

**What Makes This Intelligent**:

- Agent learns methodology from examples
- Agent decides which tools to call and when
- Agent discovers things humans might miss
- Agent asks approval before executing (not just before storing HIGH)

**Next**: Run `python demo_learning.py` to see the agent demonstrate real intelligence!
