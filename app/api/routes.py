from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.graph import graph
from app.models.state import AgentState
from app.core.database import get_db
from app.models.sql_models import Ticket, AgentLog, TicketStatus

router = APIRouter()

# --- Pydantic Models for API ---
class TicketRequest(BaseModel):
    user_email: str
    issue_description: str

class TicketResponse(BaseModel):
    ticket_id: int
    user_email: str
    category: Optional[str] = None
    priority: Optional[str] = None
    final_response: Optional[str] = None
    status: str
    issue_description: Optional[str] = None
    rag_docs: Optional[List[str]] = None

class TicketListResponse(BaseModel):
    id: int
    user_email: str
    issue_description: str
    status: str
    created_at: str

class ApprovalRequest(BaseModel):
    final_response: str

# --- Routes ---

@router.get("/tickets", response_model=List[TicketListResponse])
async def list_tickets(db: AsyncSession = Depends(get_db)):
    """
    List all tickets.
    """
    result = await db.execute(select(Ticket).order_by(Ticket.id.desc()))
    tickets = result.scalars().all()
    return [
        TicketListResponse(
            id=t.id, 
            user_email=t.user_email, 
            issue_description=t.issue_description,
            status=t.status.value, 
            created_at=t.created_at.isoformat()
        ) for t in tickets
    ]

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get specific ticket details including RAG context from the latest log.
    """
    # Fetch ticket and eagerly load logs
    stmt = select(Ticket).options(selectinload(Ticket.logs)).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket = result.scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get latest log info if exists
    latest_log = ticket.logs[-1] if ticket.logs else None
    
    return TicketResponse(
        ticket_id=ticket.id,
        user_email=ticket.user_email,
        issue_description=ticket.issue_description,
        category=latest_log.category if latest_log else None,
        priority="Unknown", # Priority isn't stored in Ticket directly in current schema, could be improved
        final_response=latest_log.response if latest_log else None,
        status=ticket.status.value,
        rag_docs=latest_log.rag_docs if latest_log else []
    )

@router.post("/tickets/{ticket_id}/approve")
async def approve_ticket(ticket_id: int, approval: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    """
    Human operator approves or edits the response.
    """
    stmt = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket = result.scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update status
    ticket.status = TicketStatus.RESOLVED
    
    # Theoretically send email here...
    print(f"--- Sending Email to {ticket.user_email} ---")
    print(f"Body: {approval.final_response}")
    
    await db.commit()
    return {"status": "resolved", "message": "Ticket approved and email sent."}

@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_in: TicketRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a ticket in DB, runs the Agent Graph, and updates the DB with results.
    """
    # 1. Create Ticket in DB
    new_ticket = Ticket(
        user_email=ticket_in.user_email,
        issue_description=ticket_in.issue_description,
        status=TicketStatus.PROCESSING
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    
    ticket_id = new_ticket.id
    
    try:
        # 2. Initialize Graph State
        initial_state: AgentState = {
            "ticket_id": ticket_id,
            "user_query": ticket_in.issue_description,
            "category": "Unclassified",
            "priority": "Unknown",
            "retrieved_docs": [],
            "draft_response": "",
            "confidence_score": 0.0,
            "needs_human_review": False
        }

        # 3. Invoke Graph
        config = {"metadata": {"ticket_id": ticket_id, "user_email": ticket_in.user_email}}
        final_state = await graph.ainvoke(initial_state, config=config)

        # 4. Update Ticket Status
        status = TicketStatus.AWAITING_REVIEW if final_state["needs_human_review"] else TicketStatus.RESOLVED
        
        new_ticket.status = status
        db.add(new_ticket)
        
        # 5. Log Agent Execution
        log_entry = AgentLog(
            ticket_id=ticket_id,
            category=final_state["category"],
            rag_docs=final_state["retrieved_docs"], # automatically serialized to JSONB
            response=final_state["draft_response"],
            confidence_score=final_state["confidence_score"]
        )
        db.add(log_entry)
        
        await db.commit()

        # 6. Response
        return TicketResponse(
            ticket_id=ticket_id,
            user_email=ticket_in.user_email,
            category=final_state["category"],
            priority=final_state["priority"],
            final_response=final_state["draft_response"],
            status=status.value
        )

    except Exception as e:
        # Error Fallback
        await db.rollback() 
        # If graph fails, mark ticket as Failed
        new_ticket.status = TicketStatus.FAILED
        db.add(new_ticket)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
