# AI Realtor Backend

## Database Setup

When setting up the project for the first time:

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
cd backend
python db/init_db.py
```

4. Set up environment variables:
Create a `.env` file in the backend directory with:
```
OPENAI_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_key_here
```

5. Start the server:
```bash
python main.py
```

The server will run on http://localhost:8000

## API Documentation

- GET /api/buildings - List all buildings
- POST /api/process-bbox - Process buildings in a bounding box
- GET /api/buildings/{id} - Get a specific building
- PUT /api/buildings/{id}/approve - Approve a building
- DELETE /api/buildings/{id} - Delete a building 