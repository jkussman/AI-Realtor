#!/usr/bin/env python3
"""
Simple API server for frontend testing.
This bypasses all the complex dependencies and just serves the frontend.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.db.database import get_database
from backend.db.models import Building

# Create simple FastAPI app
app = FastAPI(title="AI Realtor API - Simple Mode")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Realtor API is running (Simple Mode)"}

@app.get("/buildings")
async def get_buildings(db: Session = Depends(get_database)):
    """Return all buildings from the database."""
    buildings = db.query(Building).all()
    return [
        {
            "id": building.id,
            "name": building.name,
            "address": building.address,
            "building_type": building.building_type,
            "approved": building.approved,
            "contact_email": building.contact_email,
            "contact_name": building.contact_name,
            "email_sent": building.email_sent,
            "reply_received": building.reply_received,
            "created_at": building.created_at.isoformat()
        }
        for building in buildings
    ]

@app.post("/process-bbox")
async def process_bounding_boxes(request: dict, db: Session = Depends(get_database)):
    """Process bounding boxes and discover buildings."""
    from agents.building_pipeline import BuildingPipeline
    
    pipeline = BuildingPipeline()
    bounding_boxes = request.get("bounding_boxes", [])
    
    # Start the building discovery process
    await pipeline.process_bounding_boxes(bounding_boxes, db)
    
    return {
        "message": "Building discovery started",
        "status": "processing",
        "bounding_boxes_count": len(bounding_boxes)
    }

@app.post("/approve-building")
async def approve_building(request: dict, db: Session = Depends(get_database)):
    """Approve a building and start contact discovery process."""
    building_id = request.get("building_id")
    if not building_id:
        return {"error": "building_id is required"}
        
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        return {"error": "Building not found"}
        
    building.approved = True
    db.commit()
    
    # Start the contact discovery process
    from agents.building_pipeline import BuildingPipeline
    pipeline = BuildingPipeline()
    await pipeline.process_approved_building(building_id, db)
    
    return {
        "message": "Building approved",
        "building_id": building_id,
        "status": "processing"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple AI Realtor API for frontend testing...")
    print("📍 Frontend should work at: http://localhost:3000")
    print("📍 API running at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 