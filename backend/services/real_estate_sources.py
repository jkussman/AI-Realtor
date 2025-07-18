"""
Real estate data sources for building information and property details.
"""

import asyncio
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time


class RealEstateDataSources:
    """
    Service for accessing various real estate data sources.
    """
    
    def __init__(self):
        self.estated_api_key = os.getenv("ESTATED_API_KEY")
        self.reonomy_api_key = os.getenv("REONOMY_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        
        # Selenium setup for web scraping
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run headless Chrome
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    async def get_property_data(self, address: str, bbox: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Get comprehensive property data from multiple sources.
        
        Args:
            address: Property address
            bbox: Bounding box for area search (optional)
            
        Returns:
            Dictionary with property data
        """
        property_data = {
            'address': address,
            'sources': []
        }
        
        # Try multiple data sources
        sources = [
            self._get_estated_data,
            self._get_reonomy_data,
            self._scrape_streeteasy,
            self._scrape_zillow,
            self._scrape_apartments_com
        ]
        
        for source_func in sources:
            try:
                data = await source_func(address, bbox)
                if data:
                    property_data.update(data)
                    property_data['sources'].append(source_func.__name__)
                    break  # Use first successful source
            except Exception as e:
                print(f"Error with {source_func.__name__}: {e}")
                continue
        
        return property_data
    
    async def _get_estated_data(self, address: str, bbox: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
        """
        Get property data from Estated API.
        
        Estated provides comprehensive property data including ownership, sales history, etc.
        """
        if not self.estated_api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.estated_api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "address": address,
                "state": "NY"
            }
            
            response = requests.get(
                "https://api.estated.com/v4/property",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_estated_response(data)
            return None
            
        except Exception as e:
            print(f"Error getting Estated data: {e}")
            return None
    
    async def _get_reonomy_data(self, address: str, bbox: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
        """
        Get property data from Reonomy API.
        
        Reonomy focuses on commercial real estate but has some residential data.
        """
        if not self.reonomy_api_key:
            return None
        
        try:
            headers = {
                "X-API-Key": self.reonomy_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "address": address,
                "state": "NY"
            }
            
            response = requests.post(
                "https://api.reonomy.com/v1/properties/search",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_reonomy_response(data)
            return None
            
        except Exception as e:
            print(f"Error getting Reonomy data: {e}")
            return None
    
    async def _scrape_streeteasy(self, address: str, bbox: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
        """
        Scrape StreetEasy for property information.
        
        WARNING: Be respectful of rate limits and terms of service.
        """
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            
            search_url = f"https://streeteasy.com/search?address={address.replace(' ', '+')}"
            driver.get(search_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            property_data = self._parse_streeteasy_html(soup)
            
            driver.quit()
            return property_data
            
        except Exception as e:
            print(f"Error scraping StreetEasy: {e}")
            return None
    
    async def _scrape_zillow(self, address: str, bbox: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
        """
        Scrape Zillow for property information.
        
        WARNING: Be respectful of rate limits and terms of service.
        """
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            
            search_url = f"https://www.zillow.com/homes/{address.replace(' ', '-')}"
            driver.get(search_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "property-card"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            property_data = self._parse_zillow_html(soup)
            
            driver.quit()
            return property_data
            
        except Exception as e:
            print(f"Error scraping Zillow: {e}")
            return None
    
    async def _scrape_apartments_com(self, address: str, bbox: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
        """
        Scrape Apartments.com for property information.
        """
        try:
            # For now, return mock data
            return await self._mock_apartments_data(address)
            
        except Exception as e:
            print(f"Error scraping Apartments.com: {e}")
            return None
    
    # Mock data functions for development
    async def _mock_estated_data(self, address: str) -> Dict[str, Any]:
        """Generate mock Estated API response."""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        return {
            'source': 'estated_api',
            'property_type': 'residential',
            'building_class': 'A',
            'year_built': 1985,
            'total_units': 120,
            'lot_size_sqft': 15000,
            'building_sqft': 180000,
            'owner_name': 'Manhattan Property Holdings LLC',
            'last_sale_date': '2019-03-15',
            'last_sale_price': 45000000,
            'assessed_value': 42000000,
            'annual_taxes': 1200000
        }
    
    async def _mock_reonomy_data(self, address: str) -> Dict[str, Any]:
        """Generate mock Reonomy API response."""
        await asyncio.sleep(0.7)  # Simulate API delay
        
        return {
            'source': 'reonomy_api',
            'property_manager': 'Metro Property Management',
            'management_company_phone': '(212) 555-0123',
            'building_amenities': ['Doorman', 'Gym', 'Roof Deck'],
            'rent_roll_data': {
                'avg_rent_per_sqft': 65,
                'occupancy_rate': 0.94
            }
        }
    
    async def _mock_streeteasy_data(self, address: str) -> Dict[str, Any]:
        """Generate mock StreetEasy scraping response."""
        await asyncio.sleep(1.0)  # Simulate scraping delay
        
        return {
            'source': 'streeteasy_scrape',
            'building_name': 'The Metropolitan',
            'neighborhood': 'Upper East Side',
            'walkability_score': 95,
            'transit_score': 88,
            'recent_listings': [
                {'unit': '12A', 'rent': 4500, 'sqft': 800, 'beds': 1, 'baths': 1},
                {'unit': '15B', 'rent': 6200, 'sqft': 1100, 'beds': 2, 'baths': 1}
            ]
        }
    
    async def _mock_zillow_data(self, address: str) -> Dict[str, Any]:
        """Generate mock Zillow scraping response."""
        await asyncio.sleep(0.8)  # Simulate scraping delay
        
        return {
            'source': 'zillow_scrape',
            'zestimate': 850000,  # For individual units
            'rent_zestimate': 4200,
            'price_history': [
                {'date': '2023-01', 'price': 820000},
                {'date': '2023-06', 'price': 850000}
            ],
            'schools_nearby': [
                {'name': 'PS 183', 'rating': 8, 'distance': '0.2 miles'},
                {'name': 'Hunter College High School', 'rating': 10, 'distance': '0.5 miles'}
            ]
        }
    
    async def _mock_apartments_data(self, address: str) -> Dict[str, Any]:
        """Generate mock Apartments.com scraping response."""
        await asyncio.sleep(0.6)  # Simulate scraping delay
        
        return {
            'source': 'apartments_com_scrape',
            'leasing_office_phone': '(212) 555-0456',
            'office_hours': 'Mon-Fri 9AM-6PM, Sat 10AM-5PM',
            'pet_policy': 'Cats and dogs allowed, $500 deposit',
            'amenities': ['Pool', 'Fitness Center', 'Concierge', 'Parking'],
            'floor_plans': [
                {'type': 'Studio', 'sqft': 450, 'rent_range': '$2800-$3200'},
                {'type': '1BR', 'sqft': 650, 'rent_range': '$3500-$4200'},
                {'type': '2BR', 'sqft': 950, 'rent_range': '$5200-$6500'}
            ]
        }
    
    def _parse_estated_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Estated API response."""
        return {
            'source': 'estated_api',
            'property_type': data.get('property', {}).get('type'),
            'building_class': data.get('property', {}).get('class'),
            'year_built': data.get('property', {}).get('year_built'),
            'total_units': data.get('property', {}).get('units'),
            'lot_size_sqft': data.get('property', {}).get('lot_size', {}).get('sq_ft'),
            'building_sqft': data.get('property', {}).get('building_size', {}).get('sq_ft'),
            'owner_name': data.get('owner', {}).get('name'),
            'last_sale_date': data.get('sales', [{}])[0].get('date'),
            'last_sale_price': data.get('sales', [{}])[0].get('price'),
            'assessed_value': data.get('assessments', [{}])[0].get('total_value'),
            'annual_taxes': data.get('taxes', [{}])[0].get('amount')
        }
    
    def _parse_reonomy_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Reonomy API response."""
        property_data = data.get('properties', [{}])[0]
        return {
            'source': 'reonomy_api',
            'property_manager': property_data.get('property_manager'),
            'management_company_phone': property_data.get('contact_phone'),
            'building_amenities': property_data.get('amenities', []),
            'rent_roll_data': {
                'avg_rent_per_sqft': property_data.get('avg_rent_per_sqft'),
                'occupancy_rate': property_data.get('occupancy_rate')
            }
        }
    
    def _parse_streeteasy_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse StreetEasy HTML content."""
        data = {}
        
        # Extract building name
        building_name = soup.find('h1', {'class': 'building-title'})
        if building_name:
            data['building_name'] = building_name.text.strip()
            
        # Extract neighborhood
        neighborhood = soup.find('div', {'class': 'neighborhood'})
        if neighborhood:
            data['neighborhood'] = neighborhood.text.strip()
            
        # Extract scores
        scores = soup.find_all('div', {'class': 'score'})
        for score in scores:
            label = score.find('span', {'class': 'label'})
            value = score.find('span', {'class': 'value'})
            if label and value:
                data[f"{label.text.strip().lower()}_score"] = int(value.text.strip())
                
        # Extract listings
        listings = []
        listing_cards = soup.find_all('div', {'class': 'listing-card'})
        for card in listing_cards:
            listing = {}
            unit = card.find('div', {'class': 'unit'})
            if unit:
                listing['unit'] = unit.text.strip()
            price = card.find('div', {'class': 'price'})
            if price:
                listing['rent'] = int(price.text.strip().replace('$', '').replace(',', ''))
            sqft = card.find('div', {'class': 'sqft'})
            if sqft:
                listing['sqft'] = int(sqft.text.strip().replace(' sqft', ''))
            beds = card.find('div', {'class': 'beds'})
            if beds:
                listing['beds'] = int(beds.text.strip().split()[0])
            baths = card.find('div', {'class': 'baths'})
            if baths:
                listing['baths'] = float(baths.text.strip().split()[0])
            listings.append(listing)
            
        data['recent_listings'] = listings
        data['source'] = 'streeteasy_scrape'
        return data
    
    def _parse_zillow_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse Zillow HTML content."""
        data = {
            'source': 'zillow_scrape'
        }
        
        # Extract Zestimate
        zestimate = soup.find('div', {'class': 'zestimate'})
        if zestimate:
            value = zestimate.find('span', {'class': 'value'})
            if value:
                data['zestimate'] = int(value.text.strip().replace('$', '').replace(',', ''))
                
        # Extract rent Zestimate
        rent_zestimate = soup.find('div', {'class': 'rent-zestimate'})
        if rent_zestimate:
            value = rent_zestimate.find('span', {'class': 'value'})
            if value:
                data['rent_zestimate'] = int(value.text.strip().replace('$', '').replace(',', ''))
                
        # Extract price history
        history = []
        price_history = soup.find_all('div', {'class': 'price-history-item'})
        for item in price_history:
            date = item.find('span', {'class': 'date'})
            price = item.find('span', {'class': 'price'})
            if date and price:
                history.append({
                    'date': date.text.strip(),
                    'price': int(price.text.strip().replace('$', '').replace(',', ''))
                })
        data['price_history'] = history
        
        # Extract nearby schools
        schools = []
        school_items = soup.find_all('div', {'class': 'school-item'})
        for item in school_items:
            name = item.find('span', {'class': 'name'})
            rating = item.find('span', {'class': 'rating'})
            distance = item.find('span', {'class': 'distance'})
            if name and rating and distance:
                schools.append({
                    'name': name.text.strip(),
                    'rating': int(rating.text.strip()),
                    'distance': distance.text.strip()
                })
        data['schools_nearby'] = schools
        
        return data
    
    async def get_property_contacts(self, address: str) -> List[Dict[str, Any]]:
        """
        Get contact information for a property from various sources.
        
        Args:
            address: Property address
            
        Returns:
            List of contact information dictionaries
        """
        contacts = []
        
        # Search multiple sources for contacts
        contact_sources = [
            self._search_property_websites,
            self._search_management_directories,
            self._search_public_records
        ]
        
        for source_func in contact_sources:
            try:
                source_contacts = await source_func(address)
                contacts.extend(source_contacts)
            except Exception as e:
                print(f"Error getting contacts from {source_func.__name__}: {e}")
        
        return contacts
    
    async def _search_property_websites(self, address: str) -> List[Dict[str, Any]]:
        """Search property management websites for contact info."""
        # Mock implementation
        return [
            {
                'source': 'property_website',
                'name': 'John Smith',
                'title': 'Property Manager',
                'email': 'jsmith@mockproperty.com',
                'phone': '(212) 555-0123'
            }
        ]
    
    async def _search_management_directories(self, address: str) -> List[Dict[str, Any]]:
        """Search property management directories."""
        # Mock implementation
        return [
            {
                'source': 'management_directory',
                'company': 'NYC Property Management',
                'contact_email': 'info@nycproperty.com',
                'phone': '(212) 555-0456'
            }
        ]
    
    async def _search_public_records(self, address: str) -> List[Dict[str, Any]]:
        """Search public records for property contacts."""
        # Mock implementation
        return [
            {
                'source': 'public_records',
                'owner': 'Building Holdings LLC',
                'registered_agent': 'Legal Services Corp',
                'address': '123 Main St, New York, NY'
            }
        ] 