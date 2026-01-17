import chromadb
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from app.models.state import AgentState
from app.agents.llm_engine import get_llm, get_structured_llm

# --- Triage Models ---
class TriageOutput(BaseModel):
    category: str = Field(description="The category of the issue (Access, Network, Billing, General)")
    priority: str = Field(description="The priority level (High, Medium, Low)")

# --- Nodes ---

async def triage_node(state: AgentState) -> Dict[str, Any]:
    """
    Classifies the user query using Ollama.
    """
    query = state["user_query"]
    
    # 1. Get LLM & Parser
    llm, parser, format_instructions = get_structured_llm(TriageOutput)
    
    # 2. Define Prompt
    prompt = PromptTemplate(
        template="Classify the IT support ticket.\n{format_instructions}\n\nTicket: {query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": format_instructions}
    )
    
    # 3. Invoke Chain
    chain = prompt | llm | parser
    try:
        result = chain.invoke({"query": query})
        print(f"--- [Triage Node] LLM Classified: {result} ---")
        return {"category": result["category"], "priority": result["priority"]}
    except Exception as e:
        print(f"Text classification failed: {e}")
        # Fallback
        return {"category": "General", "priority": "Medium"}

async def research_node(state: AgentState) -> Dict[str, Any]:
    """
    Queries local ChromaDB for relevant documents.
    """
    category = state["category"]
    query = state["user_query"]
    
    print(f"--- [Research Node] Searching for: {query} (Category: {category}) ---")
    
    try:
        # Initialize Chroma Client (Persistent)
        # Use settings for path to ensure consistency with ingestion script
        from app.core.config import settings
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        collection = client.get_or_create_collection(name="tech_docs")
        
        # Query
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        # Parse Results
        documents = results['documents'][0] if results['documents'] else []
        if not documents:
            documents = ["No specific knowledge base article found."]
            
    except Exception as e:
        print(f"RAG lookup failed: {e}")
        documents = ["Error connecting to knowledge base."]

    return {"retrieved_docs": documents}

async def drafter_node(state: AgentState) -> Dict[str, Any]:
    """
    Generates a response using the LLM and retrieved docs.
    """
    query = state["user_query"]
    docs = state["retrieved_docs"]
    docs_text = "\n\n".join(docs)
    
    llm = get_llm()
    
    prompt = PromptTemplate(
        template="""You are an IT Support Agent.
        
        Context Guidelines:
        {docs}
        
        User Query: {query}
        
        Draft a helpful, professional response based on the context above.
        If the context doesn't help, politely ask for more details.
        """,
        input_variables=["docs", "query"]
    )
    
    chain = prompt | llm
    
    try:
        response_msg = chain.invoke({"docs": docs_text, "query": query})
        # Langchain ChatModel returns a Message object, usually .content is the string
        draft = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
    except Exception as e:
        draft = f"Error generating response: {e}"
        
    print(f"--- [Drafter Node] Generated draft ---")
    return {"draft_response": draft}

async def quality_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    Basic quality check. In a real system, use an LLM-as-a-Judge here.
    """
    draft = state["draft_response"]
    
    # Simple heuristic
    if "Error" in draft or "No specific" in draft:
        confidence = 0.4
    else:
        confidence = 0.9
        
    needs_review = confidence < 0.8
    
    return {
        "confidence_score": confidence,
        "needs_human_review": needs_review
    }
