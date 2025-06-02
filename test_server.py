from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

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
def get_buildings():
    return [
        {
            "id": 1, 
            "address": "123 Test Street", 
            "approved": False, 
            "name": "Test Building 1",
            "building_type": "Commercial",
            "contact_email": "test1@example.com",
            "contact_name": "John Doe",
            "email_sent": False,
            "reply_received": False,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2, 
            "address": "456 Demo Ave", 
            "approved": True, 
            "name": "Test Building 2",
            "building_type": "Residential",
            "contact_email": "test2@example.com",
            "contact_name": "Jane Smith",
            "email_sent": True,
            "reply_received": False,
            "created_at": "2024-01-02T00:00:00Z"
        }
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
def email_status():
    return {
        "message": "Email service is operational",
        "pending_emails": 3,
        "sent_emails": 5,
        "success": True
    }

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 