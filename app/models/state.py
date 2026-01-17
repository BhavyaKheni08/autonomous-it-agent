from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    """
    State definition for the Auto-IT-Support agent graph.
    """
    ticket_id: int
    user_query: str
    category: str
    priority: str
    retrieved_docs: List[str]
    draft_response: str
    confidence_score: float
    needs_human_review: bool
