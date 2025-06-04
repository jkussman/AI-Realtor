#!/usr/bin/env python3
"""
Test script to verify OpenAI API is working.
"""

import os
from openai import OpenAI

def test_openai():
    """Test OpenAI API with a simple request."""
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    print("✅ OpenAI API key found")
    
    try:
        # Initialize client
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
        
        # Simple test request
        print("🔍 Testing OpenAI API with simple request...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, OpenAI is working!' and nothing else."}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI response: {result}")
        
        if "Hello" in result:
            print("✅ OpenAI API is working correctly!")
            return True
        else:
            print("⚠️ Unexpected OpenAI response")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

if __name__ == "__main__":
    test_openai() 