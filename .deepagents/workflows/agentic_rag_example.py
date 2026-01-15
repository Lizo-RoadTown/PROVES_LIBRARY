"""
Agentic RAG Workflow for PROVES Library
Based on LangGraph tutorial: Build a custom RAG agent

This workflow implements an agentic RAG system that can:
1. Decide when to retrieve context from the vectorstore
2. Grade retrieved documents for relevance
3. Rewrite questions if documents are irrelevant
4. Generate answers based on relevant context
"""

from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage


# ============================================================================
# Configuration
# ============================================================================

# Initialize models (using environment variables from .env)
response_model = init_chat_model("claude-sonnet-4.5", temperature=0)
grader_model = init_chat_model("claude-sonnet-4.5", temperature=0)


# ============================================================================
# Tools
# ============================================================================

@tool
def retrieve_proves_docs(query: str) -> str:
    """Search and return information from PROVES Library documentation.

    This tool queries the vectorstore for relevant documentation chunks.
    In production, this would connect to the actual pgvector database.
    """
    # TODO: Implement actual vectorstore retrieval
    # from production.core.db import get_vectorstore
    # vectorstore = get_vectorstore()
    # docs = vectorstore.similarity_search(query, k=4)
    # return "\n\n".join([doc.page_content for doc in docs])

    return "Placeholder: Would retrieve documentation here"


retriever_tool = retrieve_proves_docs


# ============================================================================
# Structured Output Schemas
# ============================================================================

class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


# ============================================================================
# Prompts
# ============================================================================

GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)

REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)


# ============================================================================
# Nodes
# ============================================================================

def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state.

    Given the question, it will decide to retrieve using the retriever tool,
    or simply respond to the user.
    """
    response = (
        response_model
        .bind_tools([retriever_tool])
        .invoke(state["messages"])
    )
    return {"messages": [response]}


def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (
        grader_model
        .with_structured_output(GradeDocuments)
        .invoke([{"role": "user", "content": prompt}])
    )
    score = response.binary_score

    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}


def generate_answer(state: MessagesState):
    """Generate an answer based on the question and retrieved context."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


# ============================================================================
# Graph Construction
# ============================================================================

def create_agentic_rag_graph():
    """Create and compile the agentic RAG graph."""

    workflow = StateGraph(MessagesState)

    # Define the nodes
    workflow.add_node(generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node(rewrite_question)
    workflow.add_node(generate_answer)

    # Define edges
    workflow.add_edge(START, "generate_query_or_respond")

    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )

    # Grade documents and route
    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,
    )

    workflow.add_edge("generate_answer", END)
    workflow.add_edge("rewrite_question", "generate_query_or_respond")

    # Compile
    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    # Create the graph
    graph = create_agentic_rag_graph()

    # Example query
    query = "What does PROVES Library say about entity extraction?"

    print("Running Agentic RAG workflow...")
    print(f"Query: {query}\n")

    for chunk in graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }
    ):
        for node, update in chunk.items():
            print(f"Update from node: {node}")
            update["messages"][-1].pretty_print()
            print("\n")
