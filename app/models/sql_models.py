from datetime import datetime
import enum
from typing import Optional, List
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    pass

class TicketStatus(str, enum.Enum):
    OPEN = "Open"
    PROCESSING = "Processing"
    AWAITING_REVIEW = "Awaiting_Review"
    RESOLVED = "Resolved"
    FAILED = "Failed"

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_email: Mapped[str] = mapped_column(String, index=True)
    issue_description: Mapped[str] = mapped_column(String)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship to logs
    logs: Mapped[List["AgentLog"]] = relationship("AgentLog", back_populates="ticket", cascade="all, delete-orphan")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rag_docs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # Using JSONB for docs list
    response: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence_score: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="logs")
