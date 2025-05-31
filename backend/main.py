"""
Main FastAPI application for AI Realtor system.
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from db.database import get_database, init_database
from db.models import Building, EmailLog
from agents.building_pipeline import BuildingPipeline
from services.gmail_api import GmailService

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Realtor API",
    description="Agentic AI system for identifying and reaching out to NYC residential buildings",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# Pydantic models for request/response
class BoundingBox(BaseModel):
    north: float
    south: float
    east: float
    west: float

class ProcessBboxRequest(BaseModel):
    bounding_boxes: List[BoundingBox]

class ApproveBuildingRequest(BaseModel):
    building_id: int

class BuildingResponse(BaseModel):
    id: int
    name: str = None
    address: str
    building_type: str
    approved: bool
    contact_email: str = None
    contact_name: str = None
    email_sent: bool
    reply_received: bool
    created_at: str
    
    class Config:
        from_attributes = True


# Initialize services
building_pipeline = BuildingPipeline()
gmail_service = GmailService()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "AI Realtor API is running"}


@app.post("/process-bbox")
async def process_bounding_boxes(
    request: ProcessBboxRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Process bounding boxes to find and enrich residential apartment buildings.
    This runs as a background task to handle potentially long-running operations.
    """
    try:
        # Start the building discovery and enrichment pipeline
        background_tasks.add_task(
            building_pipeline.process_bounding_boxes,
            request.bounding_boxes,
            db
        )
        
        return {
            "message": "Processing bounding boxes started",
            "status": "processing",
            "bounding_boxes_count": len(request.bounding_boxes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing bounding boxes: {str(e)}")


@app.post("/approve-building")
async def approve_building(
    request: ApproveBuildingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Approve a building and trigger the contact finding + email outreach flow.
    """
    try:
        # Get the building
        building = db.query(Building).filter(Building.id == request.building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        
        # Mark as approved
        building.approved = True
        db.commit()
        
        # Start the contact finding and email sending pipeline
        background_tasks.add_task(
            building_pipeline.process_approved_building,
            building.id,
            db
        )
        
        return {
            "message": "Building approved and outreach process started",
            "building_id": building.id,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving building: {str(e)}")


@app.get("/buildings", response_model=List[BuildingResponse])
async def get_buildings(db: Session = Depends(get_database)):
    """
    Get all buildings and their current status.
    """
    try:
        buildings = db.query(Building).order_by(Building.created_at.desc()).all()
        return buildings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching buildings: {str(e)}")


@app.get("/buildings/{building_id}")
async def get_building(building_id: int, db: Session = Depends(get_database)):
    """
    Get detailed information about a specific building including email logs.
    """
    try:
        building = db.query(Building).filter(Building.id == building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        
        # Get email logs for this building
        email_logs = db.query(EmailLog).filter(EmailLog.building_id == building_id).all()
        
        return {
            "building": building,
            "email_logs": email_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching building: {str(e)}")


@app.post("/webhook/email")
async def email_webhook(
    payload: Dict[Any, Any],
    db: Session = Depends(get_database)
):
    """
    Webhook endpoint to receive incoming email reply notifications.
    This will be used for Gmail push notifications in the future.
    """
    try:
        # TODO: Implement Gmail push notification handling
        # This will parse incoming webhooks and update reply status
        
        return {"message": "Webhook received", "status": "processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@app.get("/email-status")
async def check_email_status(db: Session = Depends(get_database)):
    """
    Manually check for email replies and update statuses.
    This can be called periodically or manually.
    """
    try:
        # Get all buildings that have emails sent but no replies yet
        buildings_with_emails = db.query(Building).filter(
            Building.email_sent == True,
            Building.reply_received == False
        ).all()
        
        updated_count = 0
        for building in buildings_with_emails:
            # Check for replies using Gmail service
            if gmail_service.check_for_replies(building.contact_email):
                building.reply_received = True
                updated_count += 1
        
        db.commit()
        
        return {
            "message": "Email status check completed",
            "buildings_checked": len(buildings_with_emails),
            "replies_found": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking email status: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 