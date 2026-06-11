"""Pydantic v2 schemas for agent interaction."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"


class AgentThinkingStep(BaseModel):
    type: str = "thinking"
    step: str
    message: str
    tool_call: Optional[str] = None


class AgentResultChunk(BaseModel):
    type: str = "result"
    customers: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []


class AgentTextChunk(BaseModel):
    type: str = "text"
    content: str


class AgentErrorChunk(BaseModel):
    type: str = "error"
    message: str


class GenerateMessageRequest(BaseModel):
    customer_id: int
    product: Optional[str] = None
    tone: Optional[str] = None  # formal / casual / urgent
