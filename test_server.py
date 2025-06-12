from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime

from backend.db.database import get_database
from backend.db.models import Building, EmailLog

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Request models
class BoundingBox(BaseModel):
    north: float
    south: float
    east: float
    west: float

class ProcessBboxRequest(BaseModel):
    bounding_boxes: List[BoundingBox]

class ApproveRequest(BaseModel):
    building_id: int

@app.get("/api/")
def root():
    return {"message": "Test API is working!"}

@app.get("/api/buildings")
async def get_buildings(db: Session = Depends(get_database)):
    """Return all buildings from the database."""
    buildings = db.query(Building).all()
    return [
        {
            "id": building.id,
            "address": building.address,
            "approved": building.approved,
            "name": building.name,
            "building_type": building.building_type,
            "contact_email": building.contact_email,
            "contact_name": building.contact_name,
            "email_sent": building.email_sent,
            "reply_received": building.reply_received,
            "created_at": building.created_at.isoformat()
        }
        for building in buildings
    ]

@app.get("/api/buildings/{building_id}")
def get_building(building_id: int):
    buildings = get_buildings()
    for building in buildings:
        if building["id"] == building_id:
            return building
    return {"detail": "Building not found"}

@app.post("/api/process-bbox")
def process_bbox(request: ProcessBboxRequest):
    return {
        "message": f"Processed {len(request.bounding_boxes)} bounding boxes",
        "buildings_found": 2,
        "success": True
    }

@app.post("/api/approve-building")
def approve_building(request: ApproveRequest):
    return {
        "message": f"Building {request.building_id} approved successfully",
        "success": True
    }

@app.get("/api/email-status")
async def email_status(db: Session = Depends(get_database)):
    """Return email service status and counts."""
    pending_emails = db.query(EmailLog).filter(EmailLog.sent == False).count()
    sent_emails = db.query(EmailLog).filter(EmailLog.sent == True).count()
    
    return {
        "message": "Email service is operational",
        "pending_emails": pending_emails,
        "sent_emails": sent_emails,
        "success": True
    }

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 