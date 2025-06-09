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
            self.openai_client = OpenAI(api_key=self.openai_api_key)
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
                    
                    building = {
                        "address": details.get('formatted_address', ''),
                        "name": details.get('name', ''),
                        "building_type": "residential_apartment",
                        "estimated_units": None,
                        "year_built": None,
                        "property_manager": None,
                        "neighborhood": self._get_nyc_neighborhood(
                            place['geometry']['location']['lat'],
                            place['geometry']['location']['lng']
                        ),
                        "is_mixed_use": False,
                        "total_apartments": None,
                        "has_laundry": None,
                        "amenities": [],
                        "pet_policy": None,
                        "building_style": None,
                        "stories": None,
                        "phone": details.get('formatted_phone_number'),
                        "website": details.get('website'),
                        "place_types": place_types,
                        "latitude": place['geometry']['location']['lat'],
                        "longitude": place['geometry']['location']['lng']
                    }
                    buildings.append(building)
                    
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
        Use OpenAI to verify buildings have rental units and enhance their data.
        """
        try:
            print(f"🔍 Verifying and enhancing {len(buildings)} buildings with OpenAI")
            
            # Prepare buildings data for OpenAI
            buildings_str = json.dumps([{
                "address": b.get("address", ""),
                "name": b.get("name", ""),
                "neighborhood": b.get("neighborhood", ""),
                "place_types": b.get("place_types", []),
                "phone": b.get("phone", ""),
                "website": b.get("website", ""),
                "latitude": b.get("latitude", ""),
                "longitude": b.get("longitude", "")
            } for b in buildings], indent=2)
            
            prompt = f"""Given these buildings from Google Places API:
            {buildings_str}
            
            Within these coordinates:
            North: {bbox['north']}
            South: {bbox['south']}
            East: {bbox['east']}
            West: {bbox['west']}

            For each building that has rental apartments available (can be mixed with co-ops/condos), return a JSON object with these properties:
            - address (keep original)
            - name (keep original)
            - latitude (keep original)
            - longitude (keep original)
            - estimated_units (total number of units)
            - rental_units (number of rental units, must be > 0)
            - ownership_type (e.g. "mixed_rental_coop", "all_rental", "mixed_rental_condo")
            - year_built (construction year)
            - property_manager (management company)
            - is_mixed_use (true/false)
            - has_laundry (true/false)
            - amenities (array of amenities)
            - pet_policy (policy description)
            - building_style (architectural style)
            - stories (number of floors)
            - has_rentals (must be true)
            - rental_types (array, e.g. ["market_rate", "luxury", "affordable"])
            - rental_min_price (estimated minimum monthly rent)
            - rental_max_price (estimated maximum monthly rent)

            Return ONLY valid JSON array. Include only buildings with rental units. Keep existing addresses, names, and coordinates.
            Format the response as a JSON array of objects, each object containing the above properties.
            IMPORTANT: Return ONLY the JSON array, no other text or markdown."""

            print("⏳ Calling OpenAI API to enhance buildings...")
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a NYC real estate expert. Verify buildings have rental units available and enhance with accurate details. Only include buildings with rentals. Return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
            except Exception as e:
                if "rate limit" in str(e).lower():
                    print("❌ OpenAI API rate limit exceeded. Please try again in a few seconds.")
                    raise Exception("OpenAI API rate limit exceeded")
                else:
                    print(f"❌ OpenAI API error: {e}")
                    raise Exception(f"OpenAI API error: {e}")
            
            ai_response = response.choices[0].message.content.strip()
            print(f"📋 Raw OpenAI response length: {len(ai_response)} characters")
            
            # Remove any markdown code block syntax
            if ai_response.startswith("```"):
                ai_response = ai_response.split("\n", 1)[1]  # Remove first line
            if ai_response.endswith("```"):
                ai_response = ai_response.rsplit("\n", 1)[0]  # Remove last line
            if ai_response.startswith("json"):
                ai_response = ai_response.split("\n", 1)[1]  # Remove json tag
            
            try:
                enhanced_data = json.loads(ai_response)
                if not isinstance(enhanced_data, list):
                    if isinstance(enhanced_data, dict) and "buildings" in enhanced_data:
                        enhanced_data = enhanced_data["buildings"]
                    else:
                        enhanced_data = [enhanced_data]
                
                print(f"✅ Successfully parsed enhanced data for {len(enhanced_data)} buildings")
                
                # Merge enhanced data with original buildings
                enhanced_buildings = []
                for orig in buildings:
                    # Find matching enhanced building by address
                    enhanced = next(
                        (b for b in enhanced_data 
                         if b.get("address") == orig.get("address")), 
                        None
                    )
                    
                    if enhanced and enhanced.get("has_rentals"):
                        # Merge original data with enhanced data
                        merged = orig.copy()
                        merged.update(enhanced)
                        enhanced_buildings.append(merged)
                
                print(f"✅ Enhanced {len(enhanced_buildings)} buildings with rental information")
                if not enhanced_buildings:
                    print("⚠️ No buildings with rental units found")
                    raise Exception("No buildings with rental units found")
                return enhanced_buildings
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse enhanced JSON: {e}")
                print(f"First 100 characters of response: {ai_response[:100]}")
                raise Exception(f"Failed to parse OpenAI response: {e}")
            
        except Exception as e:
            print(f"❌ Error in OpenAI enhancement: {e}")
            raise  # Re-raise the exception to be handled by the caller 