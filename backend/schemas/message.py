"""Pydantic v2 schemas for WhatsApp message generation."""

from pydantic import BaseModel
from typing import List, Optional


class MessageVariant(BaseModel):
    tone: str  # formal / casual / urgent
    content: str


class GeneratedMessage(BaseModel):
    customer_id: int
    customer_name: str
    product: str
    variants: List[MessageVariant]


class MessageGenerateResponse(BaseModel):
    success: bool
    messages: List[GeneratedMessage]
    error: Optional[str] = None
