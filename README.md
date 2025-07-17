# AI Realtor - NYC Property Prospecting System

An agentic AI system that helps identify residential apartment buildings in New York City from selected map areas, enriches building information, and automates outreach to property managers via email.

## 🏗️ System Architecture

### Backend (FastAPI + Python Agents)
- **FastAPI** server with modular agent architecture
- **SQLite** database for building and email tracking
- **Multi-step AI pipeline** for building discovery and outreach
- **Gmail API integration** for automated email sending
- **Pluggable data sources** (mock data, real estate APIs, web scraping)

### Frontend (React + Leaflet)
- **React** with TypeScript and Material-UI
- **Leaflet maps** with drawing capabilities
- **Interactive building management** interface
- **Real-time status tracking** and notifications

## 🚀 Quick Start
### Prerequisites
- Python 3.8+
- Node.js 16+
- Gmail account for email automation
- OpenAI API key (recommended)
### 1. Backend Setup
```bash
# Navigate to project root
cd AI-Realtor
# Install Python dependencies
pip install -r requirements.txt
# Copy environment template (if .env.example exists)
cp .env.example .env
# Edit .env with your API keys
# OPENAI_API_KEY=your_openai_key_here
# FROM_EMAIL=your_gmail@gmail.com
# FROM_NAME=Your Name
# Initialize database
cd backend
python -c "from db.database import init_database; init_database()"
# Start the FastAPI server
python main.py
```
The backend will be available at `http://localhost:8000`
### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend
# Install dependencies
npm install
# Start the development server
npm start
```
The frontend will be available at `http://localhost:3000`

## 📜 License

This project is for educational and development purposes. Ensure compliance with all applicable laws and terms of service when using real estate data sources and email automation.

## ⚠️ Disclaimers

- **Legal Compliance**: Ensure all outreach complies with CAN-SPAM Act and local regulations
- **Rate Limiting**: Respect API rate limits and website terms of service
- **Data Privacy**: Handle contact information responsibly
- **Testing**: Use development/sandbox environments for testing

Built with ❤️ for NYC real estate professionals and investors.
