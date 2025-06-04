"""
Agent for finding residential apartment buildings within a bounding box using OpenAI only.
"""

import asyncio
from typing import List, Dict, Any
import os
from openai import OpenAI
import json


class BuildingFinder:
    """
    Agent responsible for finding residential apartment buildings within a bounding box.
    Uses OpenAI exclusively to research actual buildings in the specified area.
    """
    
    def __init__(self):
        # Initialize OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print("✅ OpenAI API key configured for building research")
        else:
            self.openai_client = None
            print("⚠️ No OpenAI API key found")
    
    async def get_buildings_from_bbox(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find residential apartment buildings within a bounding box using OpenAI research ONLY.
        
        Args:
            bbox: Dictionary with 'north', 'south', 'east', 'west' coordinates
            
        Returns:
            List of building data dictionaries
            
        Raises:
            Exception: If OpenAI API is not configured or fails
        """
        print(f"Researching real buildings using OpenAI for bbox: {bbox}")
        
        # Validate coordinates
        if not all(key in bbox for key in ['north', 'south', 'east', 'west']):
            raise Exception("Invalid bounding box: missing coordinates")
        
        if not all(isinstance(bbox[key], (int, float)) for key in ['north', 'south', 'east', 'west']):
            raise Exception("Invalid bounding box: coordinates must be numbers")
            
        if bbox['north'] <= bbox['south'] or bbox['east'] <= bbox['west']:
            raise Exception("Invalid bounding box: incorrect coordinate ordering")
        
        # Only use OpenAI - no fallbacks
        if not self.openai_client:
            raise Exception("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        
        return await self._get_buildings_with_openai(bbox)
    
    async def _get_buildings_with_openai(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to research buildings in the given bounding box.
        """
        try:
            print(f"🔍 Researching buildings in bbox: {bbox}")
            
            prompt = f"""Given these NYC coordinates:
            North: {bbox['north']}
            South: {bbox['south']}
            East: {bbox['east']}
            West: {bbox['west']}

            Return a JSON array of 5 real residential apartment buildings that exist within this bounding box. Include realistic details for each building. Focus on large apartment buildings with many units.

            [
                {{
                    "address": "REAL_STREET_ADDRESS",
                    "name": "BUILDING_NAME",
                    "building_type": "residential_apartment",
                    "estimated_units": NUMBER_OF_UNITS,
                    "year_built": YEAR,
                    "property_manager": "MANAGEMENT_COMPANY",
                    "neighborhood": "NEIGHBORHOOD_NAME",
                    "is_mixed_use": true/false,
                    "total_apartments": NUMBER,
                    "has_laundry": true/false,
                    "amenities": ["AMENITY1", "AMENITY2"],
                    "pet_policy": "POLICY",
                    "building_style": "STYLE",
                    "stories": NUMBER
                }}
            ]

            IMPORTANT: Return ONLY valid JSON with real buildings. No explanations. Return exactly 5 buildings."""

            print("⏳ Calling OpenAI API...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a NYC real estate expert. Return only valid JSON arrays containing real buildings that exist at the specified coordinates. Always return exactly 5 buildings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"📋 Raw OpenAI response: {ai_response}")
            
            try:
                buildings_data = json.loads(ai_response)
                if not isinstance(buildings_data, list):
                    # If we got a JSON object with a buildings key, try to extract it
                    if isinstance(buildings_data, dict) and "buildings" in buildings_data:
                        buildings_data = buildings_data["buildings"]
                    else:
                        # If we got a single building object, wrap it in a list
                        buildings_data = [buildings_data]
                        
                print(f"✅ Successfully parsed JSON response with {len(buildings_data)} buildings")
                return buildings_data
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Full response: {ai_response}")
                raise Exception("Failed to parse building data from OpenAI response")
            
        except Exception as e:
            print(f"❌ Error in OpenAI API call: {e}")
            raise e
    
    def _get_nyc_neighborhood(self, lat: float, lon: float) -> str:
        """Determine NYC neighborhood based on coordinates."""
        
        # Approximate NYC neighborhood boundaries
        if lat >= 40.785 and lon >= -73.95:  # Upper East Side
            return "Upper East Side"
        elif lat >= 40.785 and lon <= -73.95:  # Upper West Side
            return "Upper West Side"
        elif 40.72 <= lat <= 40.75 and -74.01 <= lon <= -73.98:  # Greenwich Village
            return "Greenwich Village"
        elif 40.71 <= lat <= 40.73 and -73.99 <= lon <= -73.95:  # Lower East Side
            return "Lower East Side"
        elif 40.74 <= lat <= 40.76 and -74.01 <= lon <= -73.98:  # Chelsea
            return "Chelsea"
        elif 40.74 <= lat <= 40.76 and -73.98 <= lon <= -73.96:  # Murray Hill
            return "Murray Hill"
        else:
            return "NYC"
    
    def _filter_residential_apartments(self, buildings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter buildings to only include residential apartment buildings.
        """
        filtered = []
        
        for building in buildings:
            # Check if building is residential apartment type
            building_type = building.get("building_type", "").lower()
            property_type = building.get("property_type", "").lower()
            
            # Keywords that indicate residential apartment buildings
            residential_keywords = [
                "apartment", "residential", "multifamily", "rental", 
                "condo", "cooperative", "housing"
            ]
            
            if (any(keyword in building_type for keyword in residential_keywords) or
                any(keyword in property_type for keyword in residential_keywords)):
                filtered.append(building)
        
        return filtered 