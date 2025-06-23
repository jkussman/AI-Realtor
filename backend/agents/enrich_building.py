"""
Agent for enriching building data with additional metadata.
"""

import asyncio
import random
from typing import Dict, Any, Optional
import requests
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from geopy.geocoders import Nominatim
import os
import logging
import json

logger = logging.getLogger(__name__)

class BuildingEnricher:
    """
    Agent responsible for enriching building data with additional metadata.
    Uses AI and web search to gather comprehensive building information.
    """
    
    def __init__(self, llm=None):
        """Initialize the BuildingEnricher with optional LLM."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.geolocator = Nominatim(user_agent="ai_realtor")
        
        # Initialize LangChain LLM if provided or API key is available
        self.llm = llm
        if not self.llm and self.openai_api_key:
            self.llm = OpenAI(
                api_key=self.openai_api_key,
                temperature=0.1,
                model_name="gpt-4-turbo-preview"
            )
    
    async def enrich_building(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich building data with additional metadata and verify it's residential.
        
        Args:
            building_data: Basic building information
            
        Returns:
            Enriched building data dictionary
        """
        logger.info(f"Enriching building data for: {building_data.get('address')}")
        
        enriched_data = building_data.copy()
        
        # Step 1: Validate and standardize address
        enriched_data = await self._standardize_address(enriched_data)
        logger.info(f"Standardized address: {enriched_data.get('standardized_address')}, confidence: {enriched_data.get('address_confidence')}")
        
        # Step 2: Get additional property details via web search
        web_data = await self._search_building_online(enriched_data)
        logger.info(f"Web search data: {web_data}")
        enriched_data.update(web_data)
        
        # Step 3: Use AI to analyze and classify building
        if self.llm:
            ai_analysis = await self._ai_analyze_building(enriched_data)
            logger.info(f"AI analysis: {ai_analysis}")
            enriched_data.update(ai_analysis)
        
        # Step 4: Confirm it's a residential apartment building
        enriched_data['is_residential_confirmed'] = self._confirm_residential(enriched_data)
        logger.info(f"Final enriched data: {enriched_data}")
        
        return enriched_data
    
    async def _standardize_address(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize and validate the building address.
        """
        address = building_data.get('address', '')
        
        try:
            # Use geocoding to standardize address
            location = self.geolocator.geocode(address, exactly_one=True)
            
            if location:
                # Extract components from the standardized address
                address_parts = location.address.split(',')
                
                # Clean and standardize the address parts
                cleaned_parts = [part.strip() for part in address_parts]
                
                # Reconstruct the address in a standard format
                # For NYC addresses, we want: Street Address, Borough, NY ZIP
                if len(cleaned_parts) >= 3:
                    street = cleaned_parts[0]
                    city_or_borough = next((part for part in cleaned_parts if any(borough in part.lower() for borough in ['manhattan', 'brooklyn', 'queens', 'bronx', 'staten island'])), 'New York')
                    state = next((part for part in cleaned_parts if 'NY' in part or 'New York' in part), 'NY')
                    zip_code = next((part for part in cleaned_parts if part.strip().isdigit() and len(part.strip()) == 5), '')
                    
                    # Construct standardized address
                    standardized_address = f"{street}, {city_or_borough}, {state}"
                    if zip_code:
                        standardized_address += f" {zip_code}"
                    
                    building_data['standardized_address'] = standardized_address
                    building_data['latitude'] = location.latitude
                    building_data['longitude'] = location.longitude
                    building_data['address_confidence'] = 'high'
                else:
                    building_data['standardized_address'] = location.address
                    building_data['latitude'] = location.latitude
                    building_data['longitude'] = location.longitude
                    building_data['address_confidence'] = 'medium'
            else:
                building_data['address_confidence'] = 'low'
                
        except Exception as e:
            print(f"Error standardizing address: {e}")
            building_data['address_confidence'] = 'error'
        
        return building_data
    
    async def _search_building_online(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for building information online using web search APIs.
        """
        address = building_data.get('address', '')
        web_data = {}
        
        try:
            if self.serpapi_key:
                # Use SerpAPI for web search
                web_data = await self._serpapi_search(address)
            else:
                # Use mock data for development
                web_data = await self._mock_web_search(address)
                
        except Exception as e:
            print(f"Error searching building online: {e}")
            web_data = await self._mock_web_search(address)
        
        return web_data
    
    async def _serpapi_search(self, address: str) -> Dict[str, Any]:
        """
        Search for building information using SerpAPI.
        """
        try:
            # Search for building information
            search_query = f"{address} apartment building property manager contact"
            
            params = {
                "q": search_query,
                "location": "New York, NY",
                "api_key": self.serpapi_key,
                "num": 10
            }
            
            # response = requests.get("https://serpapi.com/search", params=params)
            # results = response.json()
            
            # For now, return mock data
            return await self._mock_web_search(address)
            
        except Exception as e:
            print(f"Error with SerpAPI search: {e}")
            return await self._mock_web_search(address)
    
    async def _mock_web_search(self, address: str) -> Dict[str, Any]:
        """
        Generate mock web search results for development.
        """
        # Simulate web search delay
        await asyncio.sleep(0.5)
        
        # Generate realistic building metadata
        mock_data = {
            'name': f"The {random.choice(['Metropolitan', 'Hudson', 'Lincoln', 'Central', 'Plaza'])} Apartments",
            'number_of_units': random.randint(50, 300),
            'year_built': random.randint(1960, 2010),
            'square_footage': random.randint(500000, 2000000),
            'amenities': random.sample([
                'Doorman', 'Gym', 'Rooftop', 'Laundry', 'Parking', 
                'Pet Friendly', 'Pool', 'Concierge', 'Storage'
            ], k=random.randint(3, 6)),
            'building_class': random.choice(['Class A', 'Class B', 'Class C']),
            'rent_stabilized': random.choice([True, False]),
            'web_search_confidence': 'mock_data'
        }
        
        return mock_data
    
    async def _ai_analyze_building(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze building data and extract insights."""
        try:
            prompt = f"""
                Analyze the following building data and provide insights:
                
                Building Data: {building_data}
                
                Please analyze and respond with:
                1. Building type classification (residential_apartment, commercial, mixed_use, etc.)
                2. Estimated property manager type (large company, small local, individual)
                3. Investment attractiveness (high, medium, low)
                4. Any notable features or concerns
                
                Format your response as JSON with keys: building_type, manager_type, investment_rating, notes
                """
            
            logger.info(f"OpenAI prompt: {prompt}")
            
            # Use chat completions endpoint
            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are a real estate analysis expert. Analyze the building data and provide structured insights."},
                {"role": "user", "content": prompt}
            ])
            
            try:
                # Parse the JSON response
                insights = json.loads(response.content)
                logger.info(f"AI analysis response: {insights}")
                
                return {
                    "ai_building_type": insights.get("building_type", "unknown"),
                    "ai_manager_type": insights.get("manager_type", "unknown"),
                    "ai_investment_rating": insights.get("investment_rating", "unknown"),
                    "ai_notes": insights.get("notes", ""),
                    "ai_confidence": "high"  # We trust the model's analysis
                }
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing AI response: {str(e)}")
                return {
                    "ai_building_type": "unknown",
                    "ai_manager_type": "unknown",
                    "ai_investment_rating": "unknown",
                    "ai_notes": f"Error parsing response: {str(e)}",
                    "ai_confidence": "error"
                }
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                "ai_building_type": "unknown",
                "ai_manager_type": "unknown",
                "ai_investment_rating": "unknown",
                "ai_notes": f"Error: {str(e)}",
                "ai_confidence": "error"
            }
    
    def _confirm_residential(self, building_data: Dict[str, Any]) -> bool:
        """
        Confirm that the building is a residential apartment building.
        """
        # Check multiple indicators
        building_type = building_data.get('building_type', '').lower()
        ai_type = building_data.get('ai_building_type', '').lower()
        name = building_data.get('name', '').lower()
        
        residential_indicators = [
            'apartment' in building_type,
            'residential' in building_type,
            'apartment' in ai_type,
            'residential' in ai_type,
            'apartment' in name,
            building_data.get('number_of_units', 0) > 10  # Multi-unit building
        ]
        
        # Building is confirmed residential if at least 2 indicators are true
        return sum(residential_indicators) >= 2
    
    def _extract_building_features(self, web_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific building features from web search results.
        """
        features = {}
        
        # Extract common building features
        # This would parse actual web search results in production
        
        return features 