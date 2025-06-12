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

## 📋 Features

### 🗺️ Map-Based Building Discovery
- Draw rectangular bounding boxes on NYC map
- AI-powered building identification within selected areas
- Filter for residential apartment buildings only
- Real-time processing with status updates

### 🏢 Building Management
- View discovered buildings in organized table
- Building details including address, type, and contact info
- Approve buildings to trigger outreach workflow
- Track email status and replies

### 📧 Automated Email Outreach
- Find property manager contact information
- Generate personalized investment inquiry emails
- Send emails via Gmail API
- Track email delivery and responses

### ⚙️ Configuration & Settings
- API key management
- Email template customization
- Data source configuration
- Application preferences

## 🤖 Agent Workflow

The system uses a multi-step AI agent pipeline:

1. **Building Discovery** (`get_buildings_from_bbox`)
   - Uses real estate APIs (Estated, Reonomy) or web scraping
   - Filters for residential apartment buildings
   - Currently uses mock data for development

2. **Building Enrichment** (`enrich_building`)
   - Adds metadata (name, units, year built, etc.)
   - Validates building type and address
   - Uses AI analysis for property insights

3. **Contact Finding** (`find_contacts`)
   - Searches web for property manager contacts
   - Extracts email addresses and names
   - Multiple search strategies with confidence scoring

4. **Email Automation** (`send_email_to_contact`)
   - Generates personalized outreach emails
   - Sends via Gmail API with OAuth2
   - Logs all email activity to database

## 📊 Database Schema

### Buildings Table
- `id` - Primary key
- `name` - Building name (optional)
- `address` - Full address
- `building_type` - Type classification
- `bounding_box` - Search area coordinates
- `approved` - User approval status
- `contact_email` - Property manager email
- `contact_name` - Property manager name
- `email_sent` - Email delivery status
- `reply_received` - Response tracking
- Additional enrichment fields

### Email Logs Table
- `id` - Primary key
- `building_id` - Foreign key to buildings
- `subject` - Email subject line
- `body` - Email content
- `sent_at` - Delivery timestamp
- `status` - Delivery status
- Gmail API integration fields

## 🔧 Configuration

### Required API Keys

1. **OpenAI API** (Recommended)
   - Get from: https://platform.openai.com/api-keys
   - Used for AI building analysis and insights

2. **Gmail API** (Required for email)
   - Set up OAuth2 in Google Cloud Console
   - Download credentials.json file
   - Place in backend directory

### Optional API Keys

3. **Estated API** (Enhanced property data)
   - Property ownership and sales history
   - Set `ESTATED_API_KEY` in .env

4. **Reonomy API** (Commercial property data)
   - Building management company info
   - Set `REONOMY_API_KEY` in .env

5. **SerpAPI** (Enhanced web search)
   - Better contact finding capabilities
   - Set `SERPAPI_API_KEY` in .env

### Gmail Setup

1. Go to Google Cloud Console
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download credentials file as `gmail_credentials.json`
6. Place in backend directory
7. Run setup script: `python -c "from services.gmail_api import GmailService; GmailService().setup_oauth_credentials()"`

## 🎯 Usage Guide

### 1. Drawing Search Areas
- Go to Map page
- Use drawing tools to create rectangular bounding boxes
- Cover areas where you want to find buildings
- Submit areas for processing

### 2. Reviewing Buildings
- Go to Buildings page
- Review discovered buildings
- Check building details and type
- Approve buildings you're interested in

### 3. Managing Outreach
- Approved buildings trigger contact finding
- System searches for property manager emails
- Emails are automatically sent with investment inquiries
- Track responses in the Buildings table

### 4. Monitoring Results
- Check email status regularly
- View statistics on the Buildings page
- Follow up on conversations manually

## 🚧 Development Status

This system is currently in **development mode** with the following implementations:

### ✅ Implemented
- Complete project structure
- FastAPI backend with agent architecture
- React frontend with map interface
- Database models and API endpoints
- Gmail API integration framework
- Mock data generation for testing

### 🔄 Mock Data / Placeholders
- Building discovery (uses realistic mock buildings)
- Property data enrichment (simulated API responses)
- Contact finding (generates realistic contacts)
- Web scraping (placeholder implementations)

### 🔮 Next Steps
1. Integrate real estate APIs (Estated, Reonomy)
2. Implement web scraping for StreetEasy, Zillow
3. Add AI-powered email personalization
4. Implement reply detection and parsing
5. Add follow-up email sequences
6. Enhanced error handling and retry logic

## 🔒 Security & Compliance

- OAuth2 authentication for Gmail
- Secure API key management
- Rate limiting for web scraping
- Respect for robots.txt and ToS
- Data encryption for sensitive information

## 📝 API Documentation

With the backend running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints
- `POST /process-bbox` - Submit bounding boxes
- `GET /buildings` - List all buildings
- `POST /approve-building` - Approve building for outreach
- `GET /email-status` - Check for email replies

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Development Guidelines
- Use type hints in Python
- Follow React/TypeScript best practices
- Add error handling for all external API calls
- Test with mock data before real integrations
- Document new features and APIs

## 📜 License

This project is for educational and development purposes. Ensure compliance with all applicable laws and terms of service when using real estate data sources and email automation.

## ⚠️ Disclaimers

- **Legal Compliance**: Ensure all outreach complies with CAN-SPAM Act and local regulations
- **Rate Limiting**: Respect API rate limits and website terms of service
- **Data Privacy**: Handle contact information responsibly
- **Testing**: Use development/sandbox environments for testing

## 🆘 Troubleshooting

### Common Issues

1. **Gmail API Errors**
   - Ensure OAuth2 credentials are properly set up
   - Check that Gmail API is enabled in Google Cloud Console
   - Verify credentials.json file is in correct location

2. **Map Not Loading**
   - Check browser console for JavaScript errors
   - Ensure Leaflet CSS is properly loaded
   - Verify internet connection for map tiles

3. **API Connection Issues**
   - Check backend server is running on port 8000
   - Verify CORS settings allow frontend domain
   - Test API endpoints directly with curl or Postman

4. **Database Issues**
   - Run database initialization script
   - Check file permissions for SQLite database
   - Verify SQLAlchemy models are imported correctly

For more help, check the logs in the backend console and browser developer tools.

---

Built with ❤️ for NYC real estate professionals and investors.