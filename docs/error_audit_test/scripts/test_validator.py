"""
Test validator agent in isolation
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.curator.subagents.validator import create_validator_agent

# Create the validator
print("Creating validator agent...")
validator = create_validator_agent()

# Simple test task
task = """
Check if there are any verified entities in the database that relate to:
- Hardware components
- PROVES Kit ecosystem

Use query_verified_entities to search.
"""

print("=" * 80)
print("VALIDATOR TEST")
print("=" * 80)
print()
print("Task:", task)
print()
print("Running validator...")
print()

# Invoke the validator
result = validator.invoke({"messages": [{"role": "user", "content": task}]})

print()
print("=" * 80)
print("RESULT")
print("=" * 80)
print()
print(result['messages'][-1].content)
