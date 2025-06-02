#!/usr/bin/env python3
"""
API Testing Script for AI Realtor

This script helps you test each API connection to make sure everything is working.
Run this after setting up your .env file and API keys.

Usage: python test_apis.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API connection."""
    print("🤖 Testing OpenAI API...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OpenAI API key not found or not set properly")
        print("   Please add your OpenAI API key to the .env file")
        return False
    
    try:
        # Try to import and test OpenAI
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        if "successful" in response.choices[0].message.content.lower():
            print("✅ OpenAI API working correctly!")
            return True
        else:
            print("⚠️ OpenAI API responded but unexpected content")
            return False
            
    except ImportError:
        print("❌ OpenAI library not installed. Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def test_gmail_api():
    """Test Gmail API setup."""
    print("\n📧 Testing Gmail API...")
    
    credentials_file = "gmail_credentials.json"
    if not os.path.exists(credentials_file):
        print("❌ Gmail credentials file not found")
        print("   Please download gmail_credentials.json from Google Cloud Console")
        return False
    
    try:
        from services.gmail_api import GmailService
        gmail_service = GmailService()
        
        if gmail_service.service:
            print("✅ Gmail API service initialized successfully!")
            print("   Note: You may need to complete OAuth flow on first run")
            return True
        else:
            print("❌ Gmail API service failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Gmail API error: {e}")
        return False

def test_optional_apis():
    """Test optional APIs."""
    print("\n🏠 Testing Optional APIs...")
    
    apis_tested = 0
    apis_working = 0
    
    # Test Estated API
    estated_key = os.getenv("ESTATED_API_KEY")
    if estated_key and estated_key.strip():
        apis_tested += 1
        print("   Testing Estated API...")
        try:
            import requests
            # Simple test call to Estated API
            response = requests.get(
                "https://apis.estated.com/v4/property",
                params={"token": estated_key, "address": "1 Main St, New York, NY"},
                timeout=10
            )
            if response.status_code == 200:
                print("   ✅ Estated API working!")
                apis_working += 1
            else:
                print(f"   ❌ Estated API error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Estated API error: {e}")
    
    # Test SerpAPI
    serp_key = os.getenv("SERPAPI_API_KEY")
    if serp_key and serp_key.strip():
        apis_tested += 1
        print("   Testing SerpAPI...")
        try:
            import requests
            response = requests.get(
                "https://serpapi.com/search",
                params={"engine": "google", "q": "test", "api_key": serp_key},
                timeout=10
            )
            if response.status_code == 200:
                print("   ✅ SerpAPI working!")
                apis_working += 1
            else:
                print(f"   ❌ SerpAPI error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ SerpAPI error: {e}")
    
    if apis_tested == 0:
        print("   ℹ️ No optional API keys configured (this is fine)")
    else:
        print(f"   📊 Optional APIs: {apis_working}/{apis_tested} working")
    
    return apis_tested, apis_working

def test_database():
    """Test database connection."""
    print("\n🗄️ Testing Database...")
    
    try:
        from db.database import get_database, engine
        from db.models import Building
        
        # Test database connection
        next(get_database())
        print("✅ Database connection working!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all API tests."""
    print("🧪 AI Realtor API Testing")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create a .env file first. See SETUP_GUIDE.md for instructions.")
        sys.exit(1)
    
    print("✅ .env file found!")
    
    # Run tests
    results = []
    
    results.append(("OpenAI API", test_openai_api()))
    results.append(("Gmail API", test_gmail_api()))
    results.append(("Database", test_database()))
    
    optional_tested, optional_working = test_optional_apis()
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 TEST SUMMARY")
    print("=" * 40)
    
    required_working = 0
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
        if status:
            required_working += 1
    
    if optional_tested > 0:
        print(f"ℹ️ Optional APIs: {optional_working}/{optional_tested} working")
    
    print(f"\n📊 Required APIs: {required_working}/{len(results)} working")
    
    if required_working == len(results):
        print("\n🎉 All required APIs are working! You're ready to test your application.")
    else:
        print(f"\n⚠️ {len(results) - required_working} required API(s) need attention before testing.")
        print("Please check the setup guide and your .env file.")

if __name__ == "__main__":
    main() 