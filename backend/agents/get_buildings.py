"""
Agent for finding residential apartment buildings within a bounding box using OpenAI and Google Places API.
"""

import asyncio
from typing import List, Dict, Any
import os
from openai import OpenAI
import json
import googlemaps
from datetime import datetime


class BuildingFinder:
    """
    Agent responsible for finding residential apartment buildings within a bounding box.
    Uses both OpenAI and Google Places API to research actual buildings in the specified area.
    """
    
    def __init__(self, google_api_key: str = None):
        # Initialize OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            print("✅ OpenAI API key configured for building research")
        else:
            self.openai_client = None
            print("⚠️ No OpenAI API key found")
            
        # Initialize Google Maps client
        self.gmaps_api_key = google_api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if self.gmaps_api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.gmaps_api_key)
                print("✅ Google Maps API key configured")
            except Exception as e:
                print(f"⚠️ Error initializing Google Maps client: {e}")
                self.gmaps = None
                print("⚠️ Skipping Google services initialization for testing")
        else:
            self.gmaps = None
            print("⚠️ No Google Maps API key found")
    
    async def get_buildings_from_bbox(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find residential apartment buildings within a bounding box using both OpenAI and Google Places API.
        
        Args:
            bbox: Dictionary with 'north', 'south', 'east', 'west' coordinates
            
        Returns:
            List of building data dictionaries
            
        Raises:
            Exception: If neither API is configured or both fail
        """
        print(f"Researching real buildings for bbox: {bbox}")
        
        try:
            # First try Google Places API
            buildings = await self._get_buildings_with_google_places(bbox)
            if not buildings:
                raise Exception("No buildings found via Google Places API")
            
            # Then enhance with OpenAI
            try:
                enhanced_buildings = await self._enhance_buildings_with_openai(buildings, bbox)
                return enhanced_buildings
            except Exception as e:
                print(f"❌ OpenAI enhancement failed: {e}")
                raise  # Re-raise the exception to be handled by the caller
                
        except Exception as e:
            print(f"❌ Error finding buildings: {e}")
            raise  # Re-raise the exception to be handled by the caller
    
    async def _get_buildings_with_google_places(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Use Google Places API to find buildings in the given bounding box.
        """
        try:
            # Convert bbox to dict if it's a Pydantic model
            if hasattr(bbox, 'dict'):
                bbox = bbox.dict()
            # Calculate center point and radius for the search
            center_lat = (bbox['north'] + bbox['south']) / 2
            center_lng = (bbox['east'] + bbox['west']) / 2
            
            # Convert bounding box to location and radius (in meters)
            from math import radians, cos, sqrt
            R = 6371000  # Earth's radius in meters
            lat1, lat2 = radians(bbox['south']), radians(bbox['north'])
            lng1, lng2 = radians(bbox['west']), radians(bbox['east'])
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            radius = sqrt((R * dlat)**2 + (R * cos(lat1) * dlng)**2) / 2
            
            # Search for residential buildings using multiple keywords and types
            all_places = []
            search_types = ['apartment_complex', 'lodging']
            search_keywords = [
                'residential apartment building',
                'apartment rentals',
                'luxury apartments',
                'rental building'
            ]
            
            for search_type in search_types:
                for keyword in search_keywords:
                    try:
                        places_result = self.gmaps.places_nearby(
                            location=(center_lat, center_lng),
                            radius=min(radius, 5000),  # Max 5km radius
                            type=search_type,
                            keyword=keyword
                        )
                        
                        # Add unique places
                        for place in places_result.get('results', []):
                            if not any(p['place_id'] == place['place_id'] for p in all_places):
                                all_places.append(place)
                                
                    except Exception as e:
                        print(f"⚠️ Error in places_nearby search: {e}")
                        continue
            
            print(f"✅ Found {len(all_places)} potential buildings via Google Places API")
            
            buildings = []
            for place in all_places:
                try:
                    # Get detailed place information with correct fields
                    details = self.gmaps.place(place['place_id'], fields=[
                        'name',
                        'formatted_address',
                        'type',
                        'formatted_phone_number',
                        'website',
                        'business_status',
                        'geometry/location'
                    ])['result']
                    
                    # Get the place type from the original search result
                    place_types = place.get('types', [])
                    
                    # Initial filtering for residential buildings
                    if not any(t in place_types for t in [
                        'apartment',
                        'apartment_complex',
                        'lodging',
                        'real_estate_agency',
                        'residential'
                    ]):
                        continue
                    
                    # Skip obvious non-residential places
                    skip_types = [
                        'hotel', 'hostel', 'motel', 'resort',
                        'restaurant', 'store', 'shop', 'retail'
                    ]
                    if any(t in place_types for t in skip_types):
                        continue
                    
                    # Create building data
                    building_data = {
                        "name": details.get('name'),
                        "address": details.get('formatted_address'),
                        "phone": details.get('formatted_phone_number'),  # Changed from contact_phone to phone
                        "website": details.get('website'),
                        "place_types": place_types,
                        "latitude": details['geometry']['location']['lat'],
                        "longitude": details['geometry']['location']['lng']
                    }
                    buildings.append(building_data)
                    
                except Exception as e:
                    print(f"⚠️ Error getting place details: {e}")
                    continue
            
            print(f"✅ Found {len(buildings)} verified residential buildings via Google Places API")
            return buildings
            
        except Exception as e:
            print(f"❌ Error in Google Places API call: {e}")
            return []  # Return empty list if API fails
    
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

    async def _enhance_buildings_with_openai(self, buildings: List[Dict[str, Any]], bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to enhance building data with specific details about the building type, units, and amenities.
        Process buildings in batches to avoid timeouts.
        """
        try:
            print(f"🔍 Verifying and enhancing {len(buildings)} buildings with OpenAI")
            enhanced_buildings = []
            batch_size = 3  # Process 3 buildings at a time
            
            # Process buildings in batches
            for i in range(0, len(buildings), batch_size):
                batch = buildings[i:i + batch_size]
                print(f"📦 Processing batch {i//batch_size + 1} of {(len(buildings) + batch_size - 1)//batch_size}")
                
                # Prepare buildings data for OpenAI
                buildings_str = json.dumps([{
                    "name": b.get("name", ""),
                    "address": b.get("address", ""),
                    "website": b.get("website", "")
                } for b in batch], indent=2)
                
                prompt = f"""Here are some buildings in NYC that need verification and enhancement:
{buildings_str}

For each building, search the web to find and verify:
1. Building type (Co-op, Condo, Rental, Mixed Use)
2. Total number of apartments/units
3. Whether there have been 2-bedroom units available for rent in the past year
4. Building amenities and features
5. Any notable building characteristics or history

Return a JSON array with the enhanced building information. Each building should have these fields:
- name: string
- address: string
- building_type: string (Co-op, Condo, Rental, Mixed Use)
- total_units: number
- has_2br_rentals: boolean
- amenities: array of strings
- building_features: object with additional details
- verified: boolean (true if information was verified)
- confidence: number (0-1)
- additional_info: string (any other useful information)"""

                try:
                    messages = [
                        {"role": "system", "content": "You are a NYC real estate expert with web search capabilities. Research and enhance building details with accurate information from the web. Focus on building type, unit count, and amenities. Return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ]

                    # Initial API call with timeout
                    response = await asyncio.wait_for(
                        self._async_openai_call(messages),
                        timeout=30  # 30 second timeout
                    )

                    message = response.choices[0].message
                    messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

                    # If we got tool calls, execute them and add their results
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            if tool_call.function.name == "web_search":
                                # Execute web search
                                args = json.loads(tool_call.function.arguments)
                                search_query = args["query"]
                                print(f"🔍 Searching web for: {search_query}")
                                
                                # Mock web search results for now
                                search_results = f"Found information about {search_query}:\n"
                                search_results += "- Type: Residential apartment building\n"
                                search_results += "- Units: Multiple units available\n"
                                search_results += "- Amenities: Modern building features"
                                
                                # Add tool result back to conversation
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "content": search_results
                                })

                        # Make final API call with all context
                        final_response = await asyncio.wait_for(
                            self._async_openai_call(messages, response_format={"type": "json_object"}),
                            timeout=30  # 30 second timeout
                        )
                        
                        # Get the final JSON response
                        final_content = final_response.choices[0].message.content
                        print(f"📋 Raw OpenAI response length: {len(final_content)} characters")
                        print(f"First 100 characters of response: {final_content[:100]}")
                        
                        try:
                            enhanced_data = json.loads(final_content)
                            if isinstance(enhanced_data, dict):
                                if "error" in enhanced_data:
                                    print(f"⚠️ Received string instead of dict: {enhanced_data['error']}")
                                    continue
                                elif "buildings" in enhanced_data:
                                    enhanced_data = enhanced_data["buildings"]
                                    
                            # Convert to list if single building
                            if not isinstance(enhanced_data, list):
                                enhanced_data = [enhanced_data]
                                
                            # Add enhanced buildings to results
                            enhanced_buildings.extend(enhanced_data)
                            
                        except json.JSONDecodeError as e:
                            print(f"❌ Failed to parse JSON response: {e}")
                            continue
                            
                except asyncio.TimeoutError:
                    print("❌ OpenAI API call timed out")
                    continue
                except Exception as e:
                    print(f"❌ Error processing batch: {e}")
                    continue
                
                # Add a small delay between batches
                await asyncio.sleep(1)
            
            return enhanced_buildings
            
        except Exception as e:
            print(f"❌ Error in OpenAI enhancement: {e}")
            return []

    async def _async_openai_call(self, messages, response_format=None):
        """Helper method to make async OpenAI API calls"""
        kwargs = {
            "model": "gpt-4-turbo-preview",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2000,
            "tools": [{
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }]
        }
        
        if response_format:
            kwargs["response_format"] = response_format
            
        return await self.openai_client.chat.completions.create(**kwargs) 