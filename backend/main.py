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
import signal
import sys
import socket
from dotenv import load_dotenv
from sqlalchemy import or_, and_
import json

from db.database import get_database, init_database
from db.models import Building, EmailLog
from agents.building_pipeline import BuildingPipeline
from agents.get_buildings import BuildingFinder
# Commenting out Gmail service for now
# from services.gmail_api import GmailService
from api.endpoints.contacts import router as contacts_router

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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# Initialize services
# gmail_service = GmailService()  # Commenting out for now
building_pipeline = BuildingPipeline()
building_finder = BuildingFinder()

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
    standardized_address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    building_type: str
    bounding_box: Optional[Dict[str, Any]] = None
    approved: bool
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    email_sent: bool
    reply_received: bool
    created_at: datetime
    updated_at: datetime
    
    # Contact confidence information
    contact_email_confidence: Optional[int] = None
    contact_source: Optional[str] = None
    contact_source_url: Optional[str] = None
    contact_verified: Optional[bool] = None
    contact_last_verified: Optional[datetime] = None
    verification_notes: Optional[str] = None
    verification_flags: Optional[List[str]] = None
    
    # Basic building info
    property_manager: Optional[str] = None
    number_of_units: Optional[int] = None
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    
    # Detailed rental information
    is_coop: bool = False
    is_mixed_use: bool = False
    total_apartments: Optional[int] = None
    two_bedroom_apartments: Optional[int] = None
    recent_2br_rent: Optional[int] = None
    rent_range_2br: Optional[str] = None
    has_laundry: bool = False
    laundry_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    pet_policy: Optional[str] = None
    building_style: Optional[str] = None
    management_company: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    recent_availability: bool = False
    rental_notes: Optional[str] = None
    neighborhood: Optional[str] = None
    stories: Optional[int] = None
    
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
                    try:
                        # Ensure building_data is a dictionary
                        if isinstance(building_data, str):
                            print(f"⚠️ Received string instead of dict: {building_data[:100]}")
                            continue

                        # Check for duplicates before creating
                        address = building_data.get('address')
                        name = building_data.get('name')
                        standardized_address = building_data.get('standardized_address')
                        
                        if not address and not name:
                            print(f"⚠️ Skipping building with no address or name: {building_data}")
                            continue

                        # Query for existing buildings with exact address match
                        existing_building = db.query(Building).filter(
                            or_(
                                Building.address == address if address else False,
                                Building.standardized_address == standardized_address if standardized_address else False,
                                Building.name == name if name else False
                            )
                        ).first()

                        if existing_building:
                            print(f"⚠️ Skipping duplicate building: {address or name}")
                            continue

                        # Create new building record
                        new_building = Building(
                            name=name,
                            address=address,
                            standardized_address=standardized_address,
                            latitude=building_data.get('latitude'),
                            longitude=building_data.get('longitude'),
                            building_type=building_data.get('building_type', 'residential'),
                            bounding_box=json.dumps(bbox_dict),
                            approved=False,
                            email_sent=False,
                            reply_received=False,
                            
                            # Contact information
                            contact_email=building_data.get('contact_email'),
                            contact_name=building_data.get('contact_name'),
                            contact_phone=building_data.get('phone') or building_data.get('contact_phone'),
                            website=building_data.get('website'),
                            contact_source=building_data.get('contact_source'),
                            contact_source_url=building_data.get('contact_source_url'),
                            contact_email_confidence=building_data.get('contact_email_confidence', 0),
                            contact_verified=building_data.get('contact_verified', False),
                            verification_notes=building_data.get('verification_notes'),
                            verification_flags=building_data.get('verification_flags'),
                            
                            # Basic building info
                            property_manager=building_data.get('property_manager'),
                            number_of_units=building_data.get('number_of_units'),
                            year_built=building_data.get('year_built'),
                            square_footage=building_data.get('square_footage'),
                            
                            # Detailed rental information
                            is_coop=building_data.get('is_coop', False),
                            is_mixed_use=building_data.get('is_mixed_use', False),
                            total_apartments=building_data.get('total_apartments'),
                            two_bedroom_apartments=building_data.get('two_bedroom_apartments'),
                            recent_2br_rent=building_data.get('recent_2br_rent'),
                            rent_range_2br=building_data.get('rent_range_2br'),
                            has_laundry=building_data.get('has_laundry', False),
                            laundry_type=building_data.get('laundry_type'),
                            amenities=json.dumps(building_data.get('amenities', [])),
                            pet_policy=building_data.get('pet_policy'),
                            building_style=building_data.get('building_style'),
                            management_company=building_data.get('management_company'),
                            contact_info=json.dumps(building_data.get('contact_info', {})),
                            recent_availability=building_data.get('recent_availability', False),
                            rental_notes=building_data.get('rental_notes'),
                            neighborhood=building_data.get('neighborhood'),
                            stories=building_data.get('stories')
                        )
                        
                        db.add(new_building)
                        db.commit()
                        print(f"✅ Created new building: {address or name}")
                    except Exception as e:
                        print(f"❌ Error creating building: {str(e)}")
                        db.rollback()
                        continue
            
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
# gmail_service = None
print("⚠️ Gmail service skipped for testing (Google verification needed)")
print("📧 Email features will be disabled until Gmail is set up")

# Include routers
app.include_router(contacts_router, prefix="/api/contacts", tags=["contacts"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to AI Realtor API"}

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
            # Parse JSON fields
            bounding_box = json.loads(building.bounding_box) if building.bounding_box else None
            verification_flags = json.loads(building.verification_flags) if building.verification_flags else None
            amenities = json.loads(building.amenities) if building.amenities else None
            contact_info = json.loads(building.contact_info) if building.contact_info else None
            
            building_list.append({
                "id": building.id,
                "name": building.name,
                "address": building.address,
                "standardized_address": building.standardized_address,
                "latitude": building.latitude,
                "longitude": building.longitude,
                "building_type": building.building_type,
                "bounding_box": bounding_box,
                "approved": building.approved,
                "contact_email": building.contact_email,
                "contact_name": building.contact_name,
                "contact_phone": building.contact_phone,
                "website": building.website,
                "email_sent": building.email_sent,
                "reply_received": building.reply_received,
                "created_at": building.created_at.isoformat() if building.created_at else None,
                "updated_at": building.updated_at.isoformat() if building.updated_at else None,
                
                # Contact confidence information
                "contact_email_confidence": building.contact_email_confidence,
                "contact_source": building.contact_source,
                "contact_source_url": building.contact_source_url,
                "contact_verified": building.contact_verified,
                "contact_last_verified": building.contact_last_verified.isoformat() if building.contact_last_verified else None,
                "verification_notes": building.verification_notes,
                "verification_flags": verification_flags,
                
                # Basic building info
                "property_manager": building.property_manager,
                "number_of_units": building.number_of_units,
                "year_built": building.year_built,
                "square_footage": building.square_footage,
                
                # Detailed rental information
                "is_coop": building.is_coop,
                "is_mixed_use": building.is_mixed_use,
                "total_apartments": building.total_apartments,
                "two_bedroom_apartments": building.two_bedroom_apartments,
                "recent_2br_rent": building.recent_2br_rent,
                "rent_range_2br": building.rent_range_2br,
                "has_laundry": building.has_laundry,
                "laundry_type": building.laundry_type,
                "amenities": amenities,
                "pet_policy": building.pet_policy,
                "building_style": building.building_style,
                "management_company": building.management_company,
                "contact_info": contact_info,
                "recent_availability": building.recent_availability,
                "rental_notes": building.rental_notes,
                "neighborhood": building.neighborhood,
                "stories": building.stories
            })
        
        return building_list
    except Exception as e:
        print(f"Error fetching buildings: {str(e)}")
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


@app.delete("/api/buildings/{building_id}")
async def delete_building(building_id: int, db: Session = Depends(get_database)):
    """
    Delete a specific building from the database.
    """
    try:
        # Get the building
        building = db.query(Building).filter(Building.id == building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        
        # Store building address for response
        building_address = building.address
        
        # Delete the building
        db.delete(building)
        db.commit()
        
        return {
            "message": f"Building deleted successfully",
            "building_id": building_id,
            "address": building_address,
            "status": "deleted"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting building: {str(e)}")


@app.delete("/api/buildings")
async def delete_all_buildings(db: Session = Depends(get_database)):
    """
    Delete all buildings from the database.
    """
    try:
        # Count buildings before deletion
        building_count = db.query(Building).count()
        
        if building_count == 0:
            return {
                "message": "No buildings to delete",
                "deleted_count": 0,
                "status": "empty"
            }
        
        # Delete all buildings and associated email logs
        db.query(EmailLog).delete()
        db.query(Building).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted all {building_count} buildings",
            "deleted_count": building_count,
            "status": "deleted_all"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting all buildings: {str(e)}")


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
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down server gracefully...")
        os._exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"🚀 Starting AI Realtor API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 