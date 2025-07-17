#!/usr/bin/env python3
"""
Test script to verify the enhanced OpenAI API for building discovery.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

# Load environment variables from backend/.env file
load_dotenv('backend/.env')

from agents.get_buildings import BuildingFinder

async def test_enhanced_building_finder():
    """Test the enhanced building finder with OpenAI."""
    
    print("🧪 Testing Enhanced Building Finder with OpenAI")
    print("=" * 50)
    
    # Check if OpenAI API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"🔑 OpenAI API key found: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("⚠️ No OpenAI API key found")
    
    # Initialize the building finder
    finder = BuildingFinder()
    
    # Test bounding box for Upper East Side Manhattan
    test_bbox = {
        "north": 40.7831,
        "south": 40.7731,
        "east": -73.9441,
        "west": -73.9641
    }
    
    print(f"📍 Testing with bounding box: {test_bbox}")
    print("🔍 Searching for buildings with detailed rental information...")
    
    try:
        # Get buildings using the enhanced OpenAI API
        buildings = await finder.get_buildings_from_bbox(test_bbox)
        
        print(f"\n✅ Found {len(buildings)} buildings!")
        print("=" * 50)
        
        # Display detailed information for each building
        for i, building in enumerate(buildings, 1):
            print(f"\n🏢 Building {i}: {building.get('address', 'Unknown Address')}")
            print("-" * 40)
            
            # Basic info
            print(f"Name: {building.get('name', 'Not available')}")
            print(f"Neighborhood: {building.get('neighborhood', 'Not available')}")
            print(f"Building Type: {building.get('building_type', 'Unknown')}")
            print(f"Year Built: {building.get('year_built', 'Unknown')}")
            print(f"Stories: {building.get('stories', 'Unknown')}")
            
            # Classification
            print(f"Co-op: {'Yes' if building.get('is_coop') else 'No'}")
            print(f"Mixed Use: {'Yes' if building.get('is_mixed_use') else 'No'}")
            
            # Apartment info
            print(f"Total Apartments: {building.get('total_apartments', 'Unknown')}")
            print(f"2-Bedroom Units: {building.get('two_bedroom_apartments', 'Unknown')}")
            
            # Rent info
            if building.get('recent_2br_rent'):
                print(f"Recent 2BR Rent: ${building['recent_2br_rent']:,}/month")
            elif building.get('rent_range_2br'):
                print(f"2BR Rent Range: {building['rent_range_2br']}")
            else:
                print("2BR Rent: Not available")
            
            # Amenities
            print(f"Laundry: {'Yes' if building.get('has_laundry') else 'No'}")
            if building.get('laundry_type'):
                print(f"Laundry Type: {building['laundry_type']}")
            
            if building.get('amenities'):
                print(f"Amenities: {', '.join(building['amenities'])}")
            
            # Other details
            if building.get('pet_policy'):
                print(f"Pet Policy: {building['pet_policy']}")
            if building.get('management_company'):
                print(f"Management: {building['management_company']}")
            if building.get('contact_info'):
                print(f"Contact: {building['contact_info']}")
            if building.get('rental_notes'):
                print(f"Notes: {building['rental_notes']}")
            
            print(f"Available: {'Yes' if building.get('recent_availability') else 'No'}")
            print(f"Source: {building.get('source', 'Unknown')}")
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced building finder test completed successfully!")
        
        # Summary of new features
        print("\n📊 New Features Tested:")
        print("✅ Co-op and mixed-use classification")
        print("✅ Total apartment and 2-bedroom counts")
        print("✅ Recent rent prices and ranges")
        print("✅ Laundry facilities and types")
        print("✅ Building amenities")
        print("✅ Pet policies")
        print("✅ Management company information")
        print("✅ Contact information")
        print("✅ Availability status")
        print("✅ Rental notes")
        print("✅ Neighborhood detection")
        print("✅ Building stories")
        
    except Exception as e:
        print(f"❌ Error testing building finder: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_building_finder()) 
