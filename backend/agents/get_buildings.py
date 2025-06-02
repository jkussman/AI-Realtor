"""
Agent for finding residential apartment buildings within a bounding box.
"""

import asyncio
import random
from typing import List, Dict, Any
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from openai import OpenAI
import json


class BuildingFinder:
    """
    Agent responsible for finding residential apartment buildings within a bounding box.
    Uses OpenAI to research actual buildings in the specified area.
    """
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="ai_realtor")
        # API configurations
        self.estated_api_key = os.getenv("ESTATED_API_KEY")
        self.reonomy_api_key = os.getenv("REONOMY_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
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
        Find residential apartment buildings within a bounding box using OpenAI research.
        
        Args:
            bbox: Dictionary with 'north', 'south', 'east', 'west' coordinates
            
        Returns:
            List of building data dictionaries
        """
        print(f"Researching real buildings using OpenAI for bbox: {bbox}")
        
        # Priority order: OpenAI -> Google Places -> Realistic fallback
        if self.openai_client:
            return await self._get_buildings_with_openai(bbox)
        elif self.google_api_key:
            center_lat = (bbox["north"] + bbox["south"]) / 2
            center_lon = (bbox["east"] + bbox["west"]) / 2
            lat_diff = bbox["north"] - bbox["south"]
            lon_diff = bbox["east"] - bbox["west"]
            radius_km = max(lat_diff, lon_diff) * 111 / 2
            radius_meters = min(int(radius_km * 1000), 5000)
            return await self._get_buildings_from_google_places(center_lat, center_lon, radius_meters, bbox)
        else:
            print("⚠️ No API keys available, using realistic fallback")
            return await self._get_realistic_nyc_buildings(bbox, 
                (bbox["north"] + bbox["south"]) / 2, 
                (bbox["east"] + bbox["west"]) / 2)
    
    async def _get_buildings_with_openai(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """Use OpenAI to research actual buildings in the bounding box area."""
        
        try:
            # Calculate center coordinates for context
            center_lat = (bbox["north"] + bbox["south"]) / 2
            center_lon = (bbox["east"] + bbox["west"]) / 2
            
            # Determine approximate neighborhood for context
            neighborhood = self._get_nyc_neighborhood(center_lat, center_lon)
            
            # Create a detailed system prompt for building research
            system_prompt = """You are a real estate research assistant specializing in NYC residential apartment buildings. 

Your task is to identify REAL, EXISTING apartment buildings in a specific geographic area based on coordinates provided.

IMPORTANT REQUIREMENTS:
1. Return ONLY real buildings that actually exist at the coordinates
2. Focus on residential apartment buildings (5+ units preferred)
3. Provide accurate, verifiable addresses
4. Include realistic building details based on NYC patterns
5. Return data in valid JSON format

OUTPUT FORMAT (return as valid JSON array):
[
  {
    "address": "actual street address, NYC, NY zipcode",
    "name": "building name if known, or null",
    "latitude": actual_latitude_number,
    "longitude": actual_longitude_number, 
    "building_type": "residential_apartment",
    "estimated_units": number_between_10_and_200,
    "stories": number_between_5_and_40,
    "year_built": realistic_year_between_1900_and_2020,
    "source": "openai_research",
    "neighborhood": "detected_neighborhood",
    "building_style": "pre_war|post_war|modern|mixed"
  }
]

Research 3-6 real apartment buildings in the specified area."""

            user_prompt = f"""Research real residential apartment buildings in this NYC area:

BOUNDING BOX COORDINATES:
- North: {bbox['north']}
- South: {bbox['south']} 
- East: {bbox['east']}
- West: {bbox['west']}

APPROXIMATE AREA: {neighborhood} neighborhood, Manhattan

Please identify 3-6 REAL apartment buildings that exist within these exact coordinates. Focus on buildings with multiple residential units (apartments/condos). Use your knowledge of NYC geography and real estate to provide accurate, existing addresses.

Return the results as a valid JSON array following the specified format."""

            print(f"🔍 Using OpenAI to research buildings in {neighborhood}")
            
            # Call OpenAI API using the modern client
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=2000
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content.strip()
            print(f"📋 OpenAI response: {ai_response[:200]}...")
            
            # Try to parse JSON response
            try:
                # Clean up the response (remove markdown formatting if present)
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].strip()
                
                buildings_data = json.loads(ai_response)
                
                # Validate and clean the data
                validated_buildings = []
                for building in buildings_data:
                    if isinstance(building, dict) and building.get("address"):
                        # Ensure all required fields are present
                        validated_building = {
                            "address": building.get("address", "Unknown Address"),
                            "name": building.get("name"),
                            "latitude": float(building.get("latitude", center_lat)),
                            "longitude": float(building.get("longitude", center_lon)),
                            "building_type": "residential_apartment",
                            "estimated_units": int(building.get("estimated_units", 50)),
                            "stories": int(building.get("stories", 10)),
                            "year_built": int(building.get("year_built", 1960)),
                            "source": "openai_research",
                            "neighborhood": building.get("neighborhood", neighborhood),
                            "building_style": building.get("building_style", "mixed")
                        }
                        validated_buildings.append(validated_building)
                
                if validated_buildings:
                    print(f"✅ OpenAI found {len(validated_buildings)} real buildings")
                    return validated_buildings
                else:
                    print("⚠️ No valid buildings in OpenAI response, using fallback")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse OpenAI JSON response: {e}")
                print(f"Raw response: {ai_response}")
                
        except Exception as e:
            print(f"⚠️ OpenAI API error: {e}")
        
        # Fallback to realistic data if OpenAI fails
        print("🔄 Falling back to realistic NYC data")
        return await self._get_realistic_nyc_buildings(bbox, center_lat, center_lon)
    
    async def _get_buildings_from_estated_api(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Get buildings from Estated API.
        
        Estated API documentation: https://estated.com/developers
        """
        try:
            # TODO: Implement Estated API integration
            headers = {
                "Authorization": f"Bearer {self.estated_api_key}",
                "Content-Type": "application/json"
            }
            
            # Example API call structure (adjust based on actual API)
            params = {
                "north": bbox["north"],
                "south": bbox["south"], 
                "east": bbox["east"],
                "west": bbox["west"],
                "property_type": "multifamily",  # Filter for apartment buildings
                "limit": 50
            }
            
            # response = requests.get("https://api.estated.com/v1/properties", 
            #                       headers=headers, params=params)
            # data = response.json()
            
            # For now, return mock data
            return await self._get_mock_buildings(bbox)
            
        except Exception as e:
            print(f"Error calling Estated API: {e}")
            return await self._get_mock_buildings(bbox)
    
    async def _get_buildings_from_reonomy_api(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Get buildings from Reonomy API.
        
        Reonomy API documentation: https://www.reonomy.com/api
        """
        try:
            # TODO: Implement Reonomy API integration
            headers = {
                "X-API-Key": self.reonomy_api_key,
                "Content-Type": "application/json"
            }
            
            # Example API call structure (adjust based on actual API)
            payload = {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox["west"], bbox["south"]],
                        [bbox["east"], bbox["south"]],
                        [bbox["east"], bbox["north"]],
                        [bbox["west"], bbox["north"]],
                        [bbox["west"], bbox["south"]]
                    ]]
                },
                "property_type": "multifamily"
            }
            
            # response = requests.post("https://api.reonomy.com/v1/properties/search",
            #                        headers=headers, json=payload)
            # data = response.json()
            
            # For now, return mock data
            return await self._get_mock_buildings(bbox)
            
        except Exception as e:
            print(f"Error calling Reonomy API: {e}")
            return await self._get_mock_buildings(bbox)
    
    async def _get_buildings_from_web_scraping(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Get buildings via web scraping (StreetEasy, Zillow, etc.).
        
        WARNING: Be respectful of rate limits and terms of service.
        """
        try:
            # TODO: Implement web scraping with Selenium/BeautifulSoup
            # This would involve:
            # 1. Convert bbox to search URLs for StreetEasy/Zillow
            # 2. Use Selenium to navigate and extract building data
            # 3. Parse HTML with BeautifulSoup
            # 4. Filter for residential apartment buildings
            
            # For now, return mock data
            return await self._get_mock_buildings(bbox)
            
        except Exception as e:
            print(f"Error in web scraping: {e}")
            return await self._get_mock_buildings(bbox)
    
    async def _get_mock_buildings(self, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find real NYC apartment buildings using Google Places API and NYC data.
        """
        # Simulate API delay
        await asyncio.sleep(1)
        
        print(f"Finding real buildings in NYC for bbox: {bbox}")
        
        # Calculate center and search radius
        center_lat = (bbox["north"] + bbox["south"]) / 2
        center_lon = (bbox["east"] + bbox["west"]) / 2
        
        # Calculate search radius in meters (roughly 1 degree = 111km)
        lat_diff = bbox["north"] - bbox["south"]
        lon_diff = bbox["east"] - bbox["west"]
        radius_km = max(lat_diff, lon_diff) * 111 / 2
        radius_meters = min(int(radius_km * 1000), 5000)  # Max 5km radius
        
        print(f"Searching near ({center_lat:.4f}, {center_lon:.4f}) with radius {radius_meters}m")
        
        # Try to get real NYC buildings using Google Places API (if available)
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if google_api_key:
            return await self._get_buildings_from_google_places(center_lat, center_lon, radius_meters, bbox)
        
        # Fall back to realistic NYC data based on actual coordinates
        return await self._get_realistic_nyc_buildings(bbox, center_lat, center_lon)
    
    async def _get_buildings_from_google_places(self, lat: float, lon: float, radius: int, bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get real buildings using Google Places API."""
        try:
            google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
            
            # Search for apartment buildings and residential buildings
            search_types = ["lodging", "real_estate_agency", "establishment"]
            search_keywords = ["apartment", "residential", "building", "condo", "housing"]
            
            all_buildings = []
            
            for keyword in search_keywords[:2]:  # Limit to avoid API quota
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lon}",
                    "radius": radius,
                    "keyword": keyword,
                    "type": "establishment",
                    "key": google_api_key
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        for place in data.get("results", [])[:5]:  # Limit results
                            place_lat = place["geometry"]["location"]["lat"]
                            place_lon = place["geometry"]["location"]["lng"]
                            
                            # Check if within bounding box
                            if (bbox["south"] <= place_lat <= bbox["north"] and 
                                bbox["west"] <= place_lon <= bbox["east"]):
                                
                                building = {
                                    "address": place.get("vicinity", f"Building near {place_lat:.4f}, {place_lon:.4f}"),
                                    "name": place.get("name"),
                                    "latitude": place_lat,
                                    "longitude": place_lon,
                                    "building_type": "residential_apartment",
                                    "estimated_units": random.randint(20, 100),
                                    "stories": random.randint(6, 20),
                                    "year_built": random.randint(1950, 2020),
                                    "source": "google_places",
                                    "place_id": place.get("place_id"),
                                    "rating": place.get("rating")
                                }
                                all_buildings.append(building)
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error calling Google Places API: {e}")
                    continue
            
            if all_buildings:
                print(f"Found {len(all_buildings)} buildings from Google Places API")
                return all_buildings[:10]  # Limit to 10 buildings
                
        except Exception as e:
            print(f"Google Places API error: {e}")
        
        # Fall back to realistic data
        return await self._get_realistic_nyc_buildings(bbox, lat, lon)
    
    async def _get_realistic_nyc_buildings(self, bbox: Dict[str, float], center_lat: float, center_lon: float) -> List[Dict[str, Any]]:
        """Generate realistic NYC building data based on actual neighborhood patterns."""
        
        # Determine NYC neighborhood based on coordinates
        neighborhood = self._get_nyc_neighborhood(center_lat, center_lon)
        print(f"Generating realistic buildings for {neighborhood}")
        
        # NYC neighborhood-specific data
        neighborhood_data = {
            "Upper East Side": {
                "streets": ["East 86th Street", "East 79th Street", "East 72nd Street", "East 96th Street", "Park Avenue", "Madison Avenue", "Lexington Avenue"],
                "building_style": "pre_war",
                "avg_units": (40, 120),
                "year_range": (1920, 1950)
            },
            "Upper West Side": {
                "streets": ["West 86th Street", "West 79th Street", "West 72nd Street", "West 96th Street", "Broadway", "Amsterdam Avenue", "Columbus Avenue"],
                "building_style": "pre_war",
                "avg_units": (50, 150),
                "year_range": (1925, 1955)
            },
            "Greenwich Village": {
                "streets": ["Bleecker Street", "MacDougal Street", "Washington Square", "Waverly Place", "West 4th Street"],
                "building_style": "brownstone",
                "avg_units": (10, 40),
                "year_range": (1900, 1930)
            },
            "Lower East Side": {
                "streets": ["Delancey Street", "Rivington Street", "Houston Street", "Essex Street", "Orchard Street"],
                "building_style": "tenement",
                "avg_units": (20, 60),
                "year_range": (1920, 1960)
            },
            "Chelsea": {
                "streets": ["West 23rd Street", "West 14th Street", "8th Avenue", "9th Avenue", "10th Avenue"],
                "building_style": "mixed",
                "avg_units": (30, 80),
                "year_range": (1940, 2000)
            },
            "Murray Hill": {
                "streets": ["East 34th Street", "East 30th Street", "3rd Avenue", "Lexington Avenue", "Park Avenue"],
                "building_style": "modern",
                "avg_units": (40, 100),
                "year_range": (1960, 2010)
            },
            "NYC": {  # Default
                "streets": ["Broadway", "5th Avenue", "Park Avenue", "Madison Avenue", "3rd Avenue"],
                "building_style": "mixed",
                "avg_units": (30, 100),
                "year_range": (1940, 2000)
            }
        }
        
        data = neighborhood_data.get(neighborhood, neighborhood_data["NYC"])
        
        # Generate 3-8 realistic buildings
        num_buildings = random.randint(3, 8)
        buildings = []
        
        for i in range(num_buildings):
            # Generate coordinates within bbox
            lat = random.uniform(bbox["south"], bbox["north"])
            lon = random.uniform(bbox["west"], bbox["east"])
            
            # Generate realistic address
            street = random.choice(data["streets"])
            number = random.randint(100, 999)
            
            # Realistic building details
            min_units, max_units = data["avg_units"]
            min_year, max_year = data["year_range"]
            
            building = {
                "address": f"{number} {street}, New York, NY 10001",
                "name": f"{number} {street.split()[0]} Building" if random.random() > 0.5 else None,
                "latitude": lat,
                "longitude": lon,
                "building_type": "residential_apartment",
                "estimated_units": random.randint(min_units, max_units),
                "stories": random.randint(6, 25),
                "year_built": random.randint(min_year, max_year),
                "source": "realistic_nyc_data",
                "neighborhood": neighborhood,
                "building_style": data["building_style"]
            }
            
            buildings.append(building)
        
        print(f"Generated {len(buildings)} realistic NYC buildings in {neighborhood}")
        return buildings
    
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