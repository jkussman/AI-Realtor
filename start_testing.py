#!/usr/bin/env python3
"""
Quick Start Script for AI Realtor Testing

This script helps you get started with testing your real APIs.
It will guide you through the setup and testing process.
"""

import os
import sys
import subprocess
import webbrowser
import time

def print_header(title):
    """Print a nice header."""
    print("\n" + "=" * 50)
    print(f"🎯 {title}")
    print("=" * 50)

def check_file_exists(filepath, description):
    """Check if a required file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description} found")
        return True
    else:
        print(f"❌ {description} missing")
        return False

def run_command(command, description):
    """Run a command and show the result."""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} successful")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    """Main testing workflow."""
    print_header("AI Realtor Quick Start")
    
    print("This script will help you test your real APIs step by step.")
    print("Let's get started! 🚀\n")
    
    # Step 1: Check project structure
    print_header("Step 1: Checking Project Structure")
    
    required_files = [
        ("backend/main.py", "Backend main file"),
        ("frontend/package.json", "Frontend package file"),
        ("requirements.txt", "Python requirements"),
    ]
    
    all_files_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing. Please check your project structure.")
        return
    
    # Step 2: Check environment setup
    print_header("Step 2: Environment Setup")
    
    env_file_exists = check_file_exists("backend/.env", ".env configuration file")
    
    if not env_file_exists:
        print("\n📝 You need to create a .env file first!")
        print("👀 Check backend/SETUP_GUIDE.md for instructions.")
        
        response = input("\nHave you created your .env file? (y/n): ").lower()
        if response != 'y':
            print("Please create your .env file first, then run this script again.")
            return
    
    # Step 3: Install dependencies
    print_header("Step 3: Installing Dependencies")
    
    print("Installing Python dependencies...")
    if run_command("pip install -r requirements.txt", "Python dependencies installation"):
        print("✅ Backend dependencies ready!")
    else:
        print("❌ Failed to install Python dependencies")
        return
    
    if os.path.exists("frontend"):
        print("\nInstalling frontend dependencies...")
        if run_command("cd frontend && npm install", "Frontend dependencies installation"):
            print("✅ Frontend dependencies ready!")
        else:
            print("⚠️ Frontend dependencies failed - you can still test the backend")
    
    # Step 4: Test API connections
    print_header("Step 4: Testing API Connections")
    
    os.chdir("backend")
    
    print("Running API tests...")
    if run_command("python test_apis.py", "API connection testing"):
        print("✅ API tests completed! Check the output above.")
    else:
        print("❌ API tests failed. Please check your .env file and API keys.")
        return
    
    # Step 5: Start services
    print_header("Step 5: Starting Services")
    
    print("🎯 Now let's start your services!")
    print("\nTo test your application:")
    print("1. Start the backend server:")
    print("   cd backend && python main.py")
    print("\n2. In a new terminal, start the frontend:")
    print("   cd frontend && npm start")
    print("\n3. Open your browser to: http://localhost:3000")
    
    start_now = input("\nWould you like to start the backend server now? (y/n): ").lower()
    
    if start_now == 'y':
        print("\n🚀 Starting backend server...")
        print("The server will start in a moment. Press Ctrl+C to stop it.")
        print("After starting, open a new terminal and run: cd frontend && npm start")
        
        time.sleep(2)
        
        # Start the backend server
        try:
            subprocess.run(["python", "main.py"])
        except KeyboardInterrupt:
            print("\n👋 Server stopped. Thanks for testing!")
    else:
        print("\n👍 You can start the servers manually when ready.")
        print("📖 See backend/TESTING_GUIDE.md for detailed testing instructions.")

if __name__ == "__main__":
    main() 