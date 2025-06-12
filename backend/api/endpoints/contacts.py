"""
API endpoints for finding building contacts.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.agents.contact_finder.contact_finder import ContactFinder

router = APIRouter()

class ContactRequest(BaseModel):
    """Request model for finding contacts."""
    address: str

class ContactResponse(BaseModel):
    """Response model for contact information."""
    input_address: str
    manager_name: Optional[str]
    manager_website: Optional[str]
    contact_email: Optional[str]
    contact_form: Optional[str]

@router.post("/find", response_model=ContactResponse)
async def find_contacts(request: ContactRequest):
    """
    Find contact information for a building.
    
    Args:
        request: ContactRequest containing the building address
        
    Returns:
        ContactResponse containing the found contact information
    """
    try:
        async with ContactFinder() as finder:
            result = await finder.find_contacts(request.address)
            return ContactResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 