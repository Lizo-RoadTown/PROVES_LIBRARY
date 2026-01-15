"""
Sequential RAG Workflow for PROVES Library
Alternative approach: Linear pipeline with explicit control flow

This workflow implements a more traditional RAG system:
1. Always retrieves context for every question
2. Processes retrieved documents in a fixed pipeline
3. Generates answer with retrieved context
4. No dynamic routing or question rewriting

Compare with agentic_rag_example.py to see the differences in approach.
"""

from typing import List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# ============================================================================
# Configuration
# ============================================================================

response_model = init_chat_model("claude-sonnet-4.5", temperature=0)


# ============================================================================
# Custom State (not MessagesState)
# ============================================================================

class RAGState(BaseModel):
    """Custom state for sequential RAG pipeline."""

    question: str = Field(description="User's original question")
    retrieved_docs: List[str] = Field(default_factory=list, description="Retrieved document chunks")
    context: str = Field(default="", description="Concatenated context from docs")
    answer: str = Field(default="", description="Final generated answer")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Helper Functions
# ============================================================================

def retrieve_documents(query: str, k: int = 4) -> List[str]:
    """Retrieve k most relevant documents for the query.

    In production, connects to pgvector database.
    """
    # TODO: Implement actual vectorstore retrieval
    # from production.core.db import get_vectorstore
    # vectorstore = get_vectorstore()
    # docs = vectorstore.similarity_search(query, k=k)
    # return [doc.page_content for doc in docs]

    return [
        f"Placeholder document 1 about: {query}",
        f"Placeholder document 2 about: {query}",
        f"Placeholder document 3 about: {query}",
    ]


# ============================================================================
# Prompts
# ============================================================================

CONTEXT_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

Rules:
- Only use information from the provided context
- If the context doesn't contain enough information, say so
- Be concise and accurate
- Cite specific parts of the context when possible
"""

ANSWER_TEMPLATE = """Context:
{context}

Question: {question}

Please provide a concise answer based on the context above."""


# ============================================================================
# Nodes (Linear Pipeline Steps)
# ============================================================================

def retrieve_step(state: RAGState) -> RAGState:
    """Step 1: Retrieve relevant documents from vectorstore."""
    print(f"[1/3] Retrieving documents for: {state.question}")

    docs = retrieve_documents(state.question, k=4)
    state.retrieved_docs = docs
    state.metadata["num_docs_retrieved"] = len(docs)

    print(f"  → Retrieved {len(docs)} documents")
    return state


def prepare_context_step(state: RAGState) -> RAGState:
    """Step 2: Prepare context from retrieved documents."""
    print("[2/3] Preparing context from retrieved documents")

    # Concatenate all retrieved documents
    context_parts = []
    for i, doc in enumerate(state.retrieved_docs, 1):
        context_parts.append(f"Document {i}:\n{doc}")

    state.context = "\n\n".join(context_parts)
    state.metadata["context_length"] = len(state.context)

    print(f"  → Context prepared ({len(state.context)} characters)")
    return state


def generate_answer_step(state: RAGState) -> RAGState:
    """Step 3: Generate answer using LLM with context."""
    print("[3/3] Generating answer")

    # Build messages
    messages = [
        SystemMessage(content=CONTEXT_SYSTEM_PROMPT),
        HumanMessage(
            content=ANSWER_TEMPLATE.format(
                context=state.context,
                question=state.question
            )
        )
    ]

    # Get response from LLM
    response = response_model.invoke(messages)
    state.answer = response.content
    state.metadata["answer_length"] = len(state.answer)

    print(f"  → Answer generated ({len(state.answer)} characters)")
    return state


# ============================================================================
# Graph Construction
# ============================================================================

def create_sequential_rag_graph():
    """Create and compile the sequential RAG graph.

    This graph has a simple linear flow:
    START → retrieve → prepare_context → generate_answer → END
    """

    workflow = StateGraph(RAGState)

    # Add nodes in sequence
    workflow.add_node("retrieve", retrieve_step)
    workflow.add_node("prepare_context", prepare_context_step)
    workflow.add_node("generate_answer", generate_answer_step)

    # Define linear edges (no conditional routing)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "prepare_context")
    workflow.add_edge("prepare_context", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    # Create the graph
    graph = create_sequential_rag_graph()

    # Example query
    query = "What does PROVES Library say about entity extraction?"

    print("=" * 70)
    print("SEQUENTIAL RAG WORKFLOW")
    print("=" * 70)
    print(f"Query: {query}\n")

    # Run the graph
    result = graph.invoke({"question": query})

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nQuestion: {result.question}")
    print(f"\nAnswer: {result.answer}")
    print(f"\nMetadata:")
    for key, value in result.metadata.items():
        print(f"  - {key}: {value}")


# ============================================================================
# Comparison Notes
# ============================================================================

"""
SEQUENTIAL vs AGENTIC RAG:

Sequential RAG (this file):
+ Simpler to understand and debug
+ Predictable execution path
+ Lower latency (no decision-making overhead)
- Always retrieves, even when not needed
- Cannot adapt to poor retrievals
- No self-correction mechanisms

Agentic RAG (agentic_rag_example.py):
+ Decides when retrieval is needed
+ Can rewrite questions if docs are irrelevant
+ More intelligent and adaptive
- More complex control flow
- Higher latency due to grading/decision steps
- Requires more careful prompt engineering

Use Sequential when:
- Questions always need context
- Retrieval quality is consistently good
- Speed is critical
- Simpler debugging is preferred

Use Agentic when:
- Some questions don't need retrieval
- Retrieval quality varies
- Self-correction is valuable
- More sophisticated behavior is needed
"""
