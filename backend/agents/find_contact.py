"""
Agent for finding contact information for building managers and property contacts.
"""

import asyncio
import random
import re
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
import json
from datetime import datetime


class ContactFinder:
    """
    Agent responsible for finding contact information for buildings.
    Uses web search and AI to find property manager contact details.
    """
    
    def __init__(self, serpapi_key: str = None, llm=None):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")
        self.llm = llm
        if not self.llm and os.getenv("OPENAI_API_KEY"):
            self.llm = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1
            )
        
        self.verify_prompt = PromptTemplate(
            input_variables=["building_info", "contact_info"],
            template="""You are an expert at verifying real estate contact information.
            Given the following building information and potential contact details, analyze the likelihood that this contact information is correct.
            
            Building Information:
            {building_info}
            
            Contact Information Found:
            {contact_info}
            
            Please analyze this information and provide a response in the following JSON format:
            {{
                "confidence_score": <number between 1-10>,
                "verification_notes": "<explanation of your confidence score>",
                "verification_flags": ["list", "of", "potential", "issues"],
                "contact_verified": <true/false based on if confidence > 7>
            }}
            
            Base your confidence score on factors like:
            - Match between contact title/role and building type
            - Professional email domain vs personal email
            - Consistency with building management company
            - Presence in professional directories
            - Recent verification dates
            
            Respond only with the JSON object, no other text."""
        )
    
    async def find_contact_for_building(self, building) -> Optional[Dict[str, Any]]:
        """
        Find contact information for a building.
        
        Args:
            building: Building object from database
            
        Returns:
            Dictionary with contact information or None if not found
        """
        print(f"Finding contact for building: {building.address}")
        
        # Try multiple search strategies
        contact_info = None
        
        # Strategy 1: Web search for property manager
        contact_info = await self._search_property_manager(building)
        
        if not contact_info:
            # Strategy 2: Search real estate websites
            contact_info = await self._search_real_estate_sites(building)
        
        if not contact_info:
            # Strategy 3: Search building management companies
            contact_info = await self._search_management_companies(building)
        
        if not contact_info:
            # Strategy 4: Use AI to generate likely contacts
            contact_info = await self._ai_generate_contacts(building)
        
        if contact_info:
            # Verify and score the contact information
            verified_info = await self._verify_contact_info(building, contact_info)
            if verified_info:
                return {
                    **contact_info,
                    **verified_info
                }
        
        return contact_info
    
    async def _verify_contact_info(self, building, contact_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI to verify contact information and assign confidence scores.
        """
        try:
            # Prepare building info for the prompt
            building_info = {
                "name": building.name,
                "address": building.address,
                "type": building.building_type,
                "management_company": building.management_company,
                "total_units": building.total_apartments
            }
            
            # Get verification from OpenAI
            response = await self.llm.ainvoke(
                self.verify_prompt.format(
                    building_info=json.dumps(building_info, indent=2),
                    contact_info=json.dumps(contact_info, indent=2)
                )
            )
            
            # Parse the response
            verification = json.loads(response)
            return {
                "contact_email_confidence": verification["confidence_score"],
                "verification_notes": verification["verification_notes"],
                "verification_flags": verification["verification_flags"],
                "contact_verified": verification["contact_verified"]
            }

        except Exception as e:
            print(f"Error in contact verification: {e}")
            return None
    
    async def _search_property_manager(self, building) -> Optional[Dict[str, Any]]:
        """
        Search for property manager contact information.
        """
        try:
            search_queries = [
                f"{building.address} property manager contact",
                f"{building.address} building manager email",
                f"{building.address} leasing office contact",
                f'"{building.name}" property management' if building.name else None
            ]
            
            search_queries = [q for q in search_queries if q]  # Remove None values
            
            for query in search_queries:
                results = await self._web_search(query)
                contact = self._extract_contact_from_results(results)
                
                if contact:
                    contact['source'] = 'property_manager_search'
                    contact['source_url'] = results[0].get('url') if results else None
                    return contact
            
            return None
            
        except Exception as e:
            print(f"Error searching property manager: {e}")
            return None
    
    async def _search_real_estate_sites(self, building) -> Optional[Dict[str, Any]]:
        """
        Search real estate websites for contact information.
        """
        try:
            # Common real estate sites to search
            sites = [
                "site:apartments.com",
                "site:zillow.com",
                "site:streeteasy.com",
                "site:rent.com"
            ]
            
            for site in sites:
                query = f"{site} {building.address} contact"
                results = await self._web_search(query)
                contact = self._extract_contact_from_results(results)
                
                if contact:
                    contact['source'] = f'real_estate_site_{site.split(":")[1]}'
                    contact['confidence'] = 75
                    return contact
            
            return None
            
        except Exception as e:
            print(f"Error searching real estate sites: {e}")
            return None
    
    async def _search_management_companies(self, building) -> Optional[Dict[str, Any]]:
        """
        Search for building management companies in the area.
        """
        try:
            # Extract neighborhood/area from address
            address_parts = building.address.split(',')
            area = address_parts[0] if address_parts else building.address
            
            search_queries = [
                f"property management companies near {area} New York",
                f"apartment building management {area} NYC contact",
                f"residential property managers {area} Manhattan"
            ]
            
            for query in search_queries:
                results = await self._web_search(query)
                contact = self._extract_contact_from_results(results)
                
                if contact:
                    contact['source'] = 'management_company_search'
                    contact['confidence'] = 60
                    return contact
            
            return None
            
        except Exception as e:
            print(f"Error searching management companies: {e}")
            return None
    
    async def _ai_generate_contacts(self, building) -> Optional[Dict[str, Any]]:
        """
        Use AI to generate likely contact information based on building data.
        """
        try:
            if not self.llm:
                return None
            
            prompt_template = PromptTemplate(
                input_variables=["building_address", "building_name"],
                template="""
                Based on the following building information, suggest the most likely 
                property management company and contact information:
                
                Building Address: {building_address}
                Building Name: {building_name}
                
                Please provide:
                1. Most likely property management company name
                2. Typical contact email format for such companies
                3. Likely contact person title (Property Manager, Leasing Manager, etc.)
                
                Format as JSON: {{"company": "...", "email": "...", "title": "..."}}
                """
            )
            
            prompt = prompt_template.format(
                building_address=building.address,
                building_name=building.name or "Unknown"
            )
            
            response = self.llm(prompt)
            try:
                return json.loads(response)
            except:
                return None
            
        except Exception as e:
            print(f"Error in AI contact generation: {e}")
            return None
    
    async def _web_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search using available APIs.
        """
        try:
            if self.serpapi_key:
                return await self._serpapi_search(query)
            return []
                
        except Exception as e:
            print(f"Error in web search: {e}")
            return []
    
    async def _serpapi_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI.
        """
        try:
            params = {
                "q": query,
                "location": "New York, NY",
                "api_key": self.serpapi_key,
                "num": 10
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            if response.status_code == 200:
                results = response.json()
                return self._parse_serpapi_results(results)
            return []
            
        except Exception as e:
            print(f"Error with SerpAPI: {e}")
            return []
            
    def _parse_serpapi_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse SerpAPI search results.
        """
        parsed_results = []
        organic_results = results.get('organic_results', [])
        
        for result in organic_results:
            parsed_result = {
                "title": result.get('title'),
                "snippet": result.get('snippet'),
                "url": result.get('link')
            }
            parsed_results.append(parsed_result)
            
        return parsed_results
    
    def _extract_contact_from_results(self, search_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract contact information from search results.
        """
        for result in search_results:
            # Extract email addresses
            emails = self._extract_emails(result.get('snippet', ''))
            
            if emails:
                # Extract potential names and titles
                name = self._extract_name_from_text(result.get('snippet', ''))
                title = self._extract_title_from_text(result.get('snippet', ''))
                
                return {
                    'email': emails[0],  # Use first email found
                    'name': name,
                    'title': title,
                    'source_url': result.get('url'),
                    'extraction_method': 'web_search'
                }
        
        return None
    
    def _extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text.
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_name_from_text(self, text: str) -> Optional[str]:
        """
        Extract potential contact names from text.
        """
        # Look for patterns like "Contact John Smith" or "Manager: Jane Doe"
        name_patterns = [
            r'Contact\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Manager:?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Leasing Agent\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """
        Extract potential job titles from text.
        """
        titles = [
            'Property Manager', 'Leasing Manager', 'Building Manager',
            'Property Management', 'Leasing Agent', 'Building Superintendent'
        ]
        
        text_lower = text.lower()
        for title in titles:
            if title.lower() in text_lower:
                return title
        
        return None 