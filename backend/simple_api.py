#!/usr/bin/env python3
"""
Simple API server for frontend testing.
This bypasses all the complex dependencies and just serves the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
async def get_buildings():
    """Return test buildings for frontend."""
    return [
        {
            "id": 1,
            "name": "Central Park West Apartments",
            "address": "123 Central Park West, New York, NY",
            "building_type": "residential_apartment",
            "approved": False,
            "contact_email": None,
            "contact_name": None,
            "email_sent": False,
            "reply_received": False,
            "created_at": "2024-06-01T12:00:00Z"
        },
        {
            "id": 2,
            "name": "Broadway Heights",
            "address": "456 Broadway, New York, NY",
            "building_type": "residential_apartment", 
            "approved": True,
            "contact_email": "manager@broadwayheights.com",
            "contact_name": "Sarah Johnson",
            "email_sent": True,
            "reply_received": False,
            "created_at": "2024-06-01T13:00:00Z"
        },
        {
            "id": 3,
            "name": "Madison Square Residences",
            "address": "789 Madison Avenue, New York, NY",
            "building_type": "residential_apartment",
            "approved": True,
            "contact_email": "info@madisonsquare.com",
            "contact_name": "Mike Chen",
            "email_sent": True,
            "reply_received": True,
            "created_at": "2024-06-01T14:00:00Z"
        }
    ]

@app.post("/process-bbox")
async def process_bounding_boxes(request: dict):
    """Mock building discovery for frontend testing."""
    return {
        "message": "Building discovery started (Demo Mode)",
        "status": "processing",
        "bounding_boxes_count": len(request.get("bounding_boxes", []))
    }

@app.post("/approve-building")
async def approve_building(request: dict):
    """Mock building approval for frontend testing."""
    return {
        "message": "Building approved (Demo Mode)",
        "building_id": request.get("building_id"),
        "status": "processing"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple AI Realtor API for frontend testing...")
    print("📍 Frontend should work at: http://localhost:3000")
    print("📍 API running at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 