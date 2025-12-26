"""
Quick test of the Curator Deep Agent
"""
import sys
import os

# Add parent scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Set up environment
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import the agent
from src.curator.agent import graph

# Test it
print("=" * 60)
print("Testing PROVES Library Curator Deep Agent")
print("=" * 60)

# Simple test
result = graph.invoke({
    "messages": [{
        "role": "user",
        "content": "List the current state of the knowledge graph using the storage agent"
    }]
})

print("\nAgent Response:")
print(result['messages'][-1].content)

print("\n" + "=" * 60)
print("Test complete! Check LangSmith for full trace:")
print("https://smith.langchain.com/")
print("=" * 60)
