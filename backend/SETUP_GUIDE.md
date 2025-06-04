# 🔧 API Setup Guide

Before you can test your real APIs, you need to set up your environment variables. Think of these as "passwords" that let your application talk to external services.

## Step 1: Create Your .env File

In the `backend` directory, create a new file called `.env` (with a dot at the beginning) and add the following content:

```
# AI Realtor Environment Configuration

# OpenAI API (Required for AI building analysis)
# OPENAI_API_KEY=your_openai_api_key_here

# Database 
DATABASE_URL=sqlite:///./ai_realtor.db

# Optional APIs (leave blank if you don't have them)
ESTATED_API_KEY=
REONOMY_API_KEY=
SERPAPI_API_KEY=

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
```

## Step 2: Get Your API Keys

### 🤖 OpenAI API Key (Required)
1. Go to: https://platform.openai.com/api-keys
2. Create an account or log in
3. Click "Create new secret key"
4. Copy the key and replace `your_openai_api_key_here` in your .env file

### 📧 Gmail API Setup (Required for email sending)
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable the Gmail API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop application"
6. Download the JSON file as `gmail_credentials.json`
7. Place it in the `backend` directory (same folder as main.py)

### 🏠 Optional Property Data APIs
These are optional but provide better building information:

- **Estated API**: Property ownership data - https://estated.com/
- **Reonomy API**: Commercial property data - https://www.reonomy.com/
- **SerpAPI**: Enhanced web search - https://serpapi.com/

## Step 3: Test Your Setup

Once you have your .env file set up, you can test if everything works! 