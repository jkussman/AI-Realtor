# 🧪 API Testing Guide

This guide will walk you through testing each API endpoint to make sure your real APIs are working correctly.

## 🚀 Quick Start Testing

### Step 1: Set Up Your Environment
1. Follow the `SETUP_GUIDE.md` to create your `.env` file
2. Get your OpenAI API key and Gmail credentials
3. Run the test script: `python test_apis.py`

### Step 2: Start Your Backend Server
```bash
cd backend
python main.py
```

You should see:
```
✅ Real services initialized successfully!
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Your Frontend (in a new terminal)
```bash
cd frontend
npm start
```

## 🔍 Testing Each API Endpoint

### 1. Health Check (Basic Test)
**What it does**: Confirms your server is running

**How to test**:
- Open browser: http://localhost:8000
- Should see: `{"message": "AI Realtor API is running"}`

**✅ Success**: You see the JSON response
**❌ Problem**: Can't connect or see error message

---

### 2. Process Bounding Boxes (Building Discovery)
**What it does**: Finds buildings in a map area you draw

**Frontend Test**:
1. Go to http://localhost:3000
2. Navigate to "Map" page
3. Use drawing tools to create a rectangle
4. Click "Process Areas"

**API Test** (using curl):
```bash
curl -X POST "http://localhost:8000/process-bbox" \
  -H "Content-Type: application/json" \
  -d '{
    "bounding_boxes": [
      {
        "north": 40.7831,
        "south": 40.7829,
        "east": -73.9654,
        "west": -73.9656
      }
    ]
  }'
```

**✅ Success**: Response like:
```json
{
  "message": "Processing bounding boxes started",
  "status": "processing",
  "bounding_boxes_count": 1
}
```

**❌ Common Problems**:
- `503 error`: API keys not set up correctly
- `500 error`: Check your OpenAI API key

---

### 3. Get Buildings (View Results)
**What it does**: Shows all discovered buildings

**Frontend Test**:
1. Go to "Buildings" page
2. Should see any buildings found from step 2

**API Test**:
```bash
curl "http://localhost:8000/buildings"
```

**✅ Success**: JSON array of buildings (may be empty if none found yet)
**❌ Problem**: Error message or can't connect

---

### 4. Approve Building (Start Email Process)
**What it does**: Triggers contact finding and email sending for a building

**Prerequisites**: You need at least one building from step 2

**Frontend Test**:
1. On "Buildings" page
2. Click "Approve" button next to a building
3. Should see status change to "Processing"

**API Test** (replace `1` with actual building ID):
```bash
curl -X POST "http://localhost:8000/approve-building" \
  -H "Content-Type: application/json" \
  -d '{"building_id": 1}'
```

**✅ Success**: Response like:
```json
{
  "message": "Building approved and outreach process started",
  "building_id": 1,
  "status": "processing"
}
```

**❌ Common Problems**:
- `404`: Building ID doesn't exist
- `503`: Services not initialized (check API keys)

---

### 5. Check Email Status
**What it does**: Checks for replies from sent emails

**API Test**:
```bash
curl "http://localhost:8000/email-status"
```

**✅ Success**: Response like:
```json
{
  "message": "Email status check completed",
  "buildings_checked": 2,
  "replies_found": 0
}
```

**❌ Problem**: Gmail API not configured

## 🐛 Common Issues and Solutions

### Issue: "503 Service Unavailable"
**Cause**: API services not initialized
**Solution**: 
1. Check your `.env` file has correct API keys
2. Run `python test_apis.py` to verify
3. Restart the backend server

### Issue: "Gmail service not available"
**Cause**: Gmail API not set up
**Solution**:
1. Download `gmail_credentials.json` from Google Cloud Console
2. Place in `backend` directory
3. Run the backend - it will guide you through OAuth setup

### Issue: "OpenAI API error"
**Cause**: Invalid or missing OpenAI API key
**Solution**:
1. Verify your OpenAI API key in `.env`
2. Check you have credits on your OpenAI account
3. Try the test script: `python test_apis.py`

### Issue: No buildings found
**Cause**: Real estate data sources might be limited
**Solution**:
1. Try different areas (Manhattan usually has more data)
2. Make your bounding box larger
3. Check the backend logs for specific errors

## 📊 Understanding the Workflow

Here's what happens when you test the full workflow:

1. **Draw area on map** → Sends bounding box coordinates
2. **Backend finds buildings** → Uses Google Places API and real estate sources
3. **Buildings appear in table** → Stored in database
4. **Approve building** → Triggers contact finding
5. **System finds contacts** → Uses web scraping and AI
6. **Email sent** → Via Gmail API
7. **Check for replies** → Monitors Gmail inbox

## 🎯 Success Criteria

Your APIs are working correctly if:
- ✅ Health check responds
- ✅ Can process bounding boxes without 503 errors
- ✅ Buildings appear in the database
- ✅ Can approve buildings without errors
- ✅ Email status check works (even if no emails sent yet)

## 🔄 Next Steps After Testing

Once your APIs are working:
1. Test with real map areas in NYC
2. Approve a few buildings to test email flow
3. Monitor the backend logs for any issues
4. Check your Gmail sent folder for outgoing emails
5. Set up periodic email checking for replies 