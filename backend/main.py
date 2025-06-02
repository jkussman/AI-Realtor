"""
Main FastAPI application for AI Realtor system.
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

from db.database import get_database, init_database
from db.models import Building, EmailLog
# Import the real services instead of using mocks
# from agents.building_pipeline import BuildingPipeline
from agents.get_buildings import BuildingFinder
# from services.gmail_api import GmailService

# Skip service imports that require Google auth for now
print("⚠️ Skipping Google services initialization for testing")

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
    name: Optional[str] = None
    address: str
    building_type: str
    approved: bool
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    email_sent: bool
    reply_received: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Enable real building discovery without Google OAuth requirements
print("✅ Initializing realistic building pipeline...")

# Create a custom pipeline that uses real building finding but skips Google services
class RealisticBuildingPipeline:
    def __init__(self):
        self.building_finder = BuildingFinder()
        print("✅ Building finder initialized")
    
    def process_bounding_boxes(self, bboxes, db):
        """Find real buildings using the BuildingFinder."""
        import asyncio
        import json
        from db.models import Building
        
        print(f"Processing {len(bboxes)} bounding boxes with realistic building finder...")
        
        buildings_created = []
        
        try:
            # Use asyncio to call the async building finder
            for bbox in bboxes:
                bbox_dict = {
                    "north": bbox.north,
                    "south": bbox.south, 
                    "east": bbox.east,
                    "west": bbox.west
                }
                
                # Get real buildings from the building finder
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                buildings_data = loop.run_until_complete(
                    self.building_finder.get_buildings_from_bbox(bbox_dict)
                )
                loop.close()
                
                # Create building records in database
                for building_data in buildings_data:
                    building = Building(
                        name=building_data.get('name'),
                        address=building_data['address'],
                        building_type=building_data.get('building_type', 'residential_apartment'),
                        bounding_box=json.dumps(bbox_dict),
                        approved=False,
                        email_sent=False,
                        reply_received=False,
                        # Store additional building details as metadata
                        property_manager=building_data.get('property_manager'),
                        number_of_units=building_data.get('estimated_units'),
                        year_built=building_data.get('year_built')
                    )
                    db.add(building)
                    buildings_created.append(building)
            
            db.commit()
            print(f"✅ Created {len(buildings_created)} realistic buildings from building finder")
            return {"status": "completed", "buildings_found": len(buildings_created)}
            
        except Exception as e:
            print(f"Error in realistic building pipeline: {e}")
            db.rollback()
            raise e
    
    def process_approved_building(self, building_id, db):
        print(f"📧 Would process building {building_id} (email features disabled)")
        # Mark building as having email sent for demo purposes
        from db.models import Building
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            building.email_sent = True
            building.contact_email = "demo@example.com"
            building.contact_name = "Demo Contact"
            db.commit()
        return {"status": "completed"}

building_pipeline = RealisticBuildingPipeline()

# Skip Gmail for testing
gmail_service = None
print("⚠️ Gmail service skipped for testing (Google verification needed)")
print("📧 Email features will be disabled until Gmail is set up")


@app.get("/api/")
async def root():
    """Health check endpoint."""
    return {"message": "AI Realtor API is running"}


@app.post("/api/process-bbox")
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
        # Check if services are properly initialized
        if building_pipeline is None:
            raise HTTPException(
                status_code=503, 
                detail="Building pipeline service not available. Please check your API keys and configuration."
            )
        
        # For real BuildingPipeline, call the async method directly
        if hasattr(building_pipeline, 'process_bounding_boxes_sync'):
            # Real BuildingPipeline with async support
            background_tasks.add_task(
                building_pipeline.process_bounding_boxes_sync,
                request.bounding_boxes,
                db
            )
        else:
            # Fallback synchronous pipeline
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


@app.post("/api/approve-building")
async def approve_building(
    request: ApproveBuildingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Approve a building and trigger the contact finding + email outreach flow.
    """
    try:
        # Check if services are properly initialized
        if building_pipeline is None:
            raise HTTPException(
                status_code=503, 
                detail="Building pipeline service not available. Please check your API keys and configuration."
            )
        
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


@app.get("/api/buildings")
async def get_buildings(db: Session = Depends(get_database)):
    """
    Get all buildings and their current status from the actual database.
    """
    try:
        # Get all buildings from database
        buildings = db.query(Building).all()
        
        # Convert to the format expected by frontend
        building_list = []
        for building in buildings:
            building_list.append({
                "id": building.id,
                "name": building.name,
                "address": building.address,
                "building_type": building.building_type,
                "approved": building.approved,
                "contact_email": building.contact_email,
                "contact_name": building.contact_name,
                "email_sent": building.email_sent,
                "reply_received": building.reply_received,
                "created_at": building.created_at.isoformat() if building.created_at else None
            })
        
        return building_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching buildings: {str(e)}")


@app.get("/api/buildings/{building_id}")
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


@app.post("/api/webhook/email")
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


@app.get("/api/email-status")
async def check_email_status(db: Session = Depends(get_database)):
    """
    Manually check for email replies and update statuses.
    This can be called periodically or manually.
    """
    try:
        # Check if services are properly initialized
        if gmail_service is None:
            # Return a mock response for testing when Gmail is not set up
            return {
                "message": "Email status check completed (Gmail service not configured)",
                "buildings_checked": 0,
                "replies_found": 0,
                "status": "testing_mode"
            }
        
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


@app.get("/test-db")
async def test_database(db: Session = Depends(get_database)):
    """Simple database test endpoint."""
    try:
        buildings = db.query(Building).all()
        return {
            "status": "success",
            "building_count": len(buildings),
            "buildings": [f"ID {b.id}: {b.address}" for b in buildings]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.delete("/api/clear-database")
async def clear_database(db: Session = Depends(get_database)):
    """Clear all buildings from database to start fresh."""
    try:
        # Delete all buildings
        deleted_count = db.query(Building).count()
        db.query(Building).delete()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Cleared {deleted_count} buildings from database",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 