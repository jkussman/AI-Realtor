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

Built with ❤️ for NYC real estate professionals and investors.
