"""
Main building pipeline that orchestrates all agent steps.
"""

import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
from sqlalchemy import or_, and_
import logging

from .get_buildings import BuildingFinder
from .enrich_building import BuildingEnricher
from .contact_finder.contact_finder import ContactFinder
# Commenting out email sender for now
# from .send_email import EmailSender
from backend.db.models import Building, ContactSource
from langchain_openai import OpenAI

logger = logging.getLogger(__name__)

class BuildingPipeline:
    """
    Main pipeline that orchestrates the building discovery and outreach process.
    """
    
    def __init__(self, google_api_key: str = None, openai_api_key: str = None):
        """Initialize the pipeline components."""
        # Initialize OpenAI client
        self.llm = OpenAI(
            api_key=openai_api_key,
            temperature=0,
            model_name="gpt-4-turbo-preview",
            tools=[{
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information about buildings and real estate.",
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
            }],
            tool_choice="auto"  # Let the model decide when to search
        )
        
        # Initialize pipeline components
        self.building_finder = BuildingFinder(google_api_key)
        self.building_enricher = BuildingEnricher(llm=self.llm)
        self.contact_finder = ContactFinder()
        # Commenting out email sender for now
        # self.email_sender = EmailSender()
    
    async def process_buildings(self, location: Dict[str, float], search_radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Process buildings through the entire pipeline.
        
        Args:
            location: Dict with 'lat' and 'lng' for the search center
            search_radius: Radius in meters to search (default 1000)
            
        Returns:
            List of processed buildings with enhanced information
        """
        try:
            # Find buildings using Google Places
            buildings = await self.building_finder.find_buildings(location, search_radius)
            print(f"Found {len(buildings)} buildings")
            
            # Process each building
            processed_buildings = []
            for building in buildings:
                try:
                    # Enrich building information
                    enriched = await self.building_enricher.enrich_building(building)
                    if enriched:
                        logger.info(f"Calling ContactFinder for address: {enriched.get('address')}")
                        contact_info = await self.contact_finder.find_contacts(enriched.get('address'))
                        logger.info(f"ContactFinder result: {contact_info}")
                        if contact_info:
                            enriched.update(contact_info)
                            
                            # Store additional contact sources if found
                            if isinstance(contact_info.get('additional_sources'), list):
                                enriched['contact_sources'] = contact_info['additional_sources']
                        
                        processed_buildings.append(enriched)
                except Exception as e:
                    print(f"Error processing building {building.get('name', 'Unknown')}: {str(e)}")
                    continue
            
            print(f"Successfully processed {len(processed_buildings)} buildings")
            return processed_buildings
            
        except Exception as e:
            print(f"Error in building pipeline: {str(e)}")
            return []
    
    async def process_bounding_boxes(self, bounding_boxes: List[dict], db: Session):
        """
        Process bounding boxes to find and enrich residential apartment buildings.
        
        Args:
            bounding_boxes: List of bounding box coordinates
            db: Database session
        """
        try:
            print(f"Processing {len(bounding_boxes)} bounding boxes...")
            
            all_buildings = []
            duplicates_found = 0
            
            for bbox in bounding_boxes:
                print(f"Processing bounding box: {bbox}")
                
                # Step 1
                buildings = await self.building_finder.get_buildings_from_bbox(bbox)
                
                for building_data in buildings:
                    try:
                        # Check for duplicates before processing
                        address = building_data.get('address')
                        name = building_data.get('name')
                        
                        # Get standardized address if available
                        standardized_address = building_data.get('standardized_address')
                        
                        # Query for existing buildings with exact address match
                        existing_building = db.query(Building).filter(
                            or_(
                                Building.address == address,  # Exact match on original address
                                Building.standardized_address == standardized_address if standardized_address else False,  # Exact match on standardized address
                                and_(
                                    Building.name == name,  # Exact match on name
                                    Building.name != None,
                                    Building.name != ""
                                ) if name else False
                            )
                        ).first()
                        
                        if existing_building:
                            print(f"\n⚠️ Duplicate building found:")
                            print(f"  - Address: {address}")
                            print(f"  - Standardized Address: {standardized_address}")
                            print(f"  - Name: {name}")
                            print(f"  - Existing ID: {existing_building.id}")
                            duplicates_found += 1
                            continue
                            
                        # Step 2: Enrich building data
                        enriched_data = await self.building_enricher.enrich_building(building_data)
                        
                        # Get the standardized address from enriched data
                        standardized_address = enriched_data.get('standardized_address')
                        
                        # Step 3: Find contact information
                        print(f"\n🔍 Finding contacts for: {enriched_data.get('name')} at {enriched_data.get('address')}")
                        contact_info = await self.contact_finder.find_contacts(enriched_data.get('address'))
                        if contact_info:
                            print(f"✅ Found contact info:")
                            print(f"  - Email: {contact_info.get('email')}")
                            print(f"  - Name: {contact_info.get('name')}")
                            print(f"  - Phone: {contact_info.get('contact_phone')}")
                            print(f"  - Title: {contact_info.get('title')}")
                            print(f"  - Source: {contact_info.get('source')}")
                            print(f"  - Confidence: {contact_info.get('contact_email_confidence')}")
                            enriched_data.update(contact_info)
                        else:
                            print(f"⚠️ No contact information found")
                        
                        # Step 4: Save to database
                        building = Building(
                            name=enriched_data.get('name'),
                            address=enriched_data['address'],
                            standardized_address=enriched_data.get('standardized_address'),
                            latitude=str(enriched_data.get('latitude')) if enriched_data.get('latitude') else None,
                            longitude=str(enriched_data.get('longitude')) if enriched_data.get('longitude') else None,
                            building_type=enriched_data.get('building_type', 'residential_apartment'),
                            bounding_box=json.dumps(bbox),
                            approved=False,
                            email_sent=False,
                            reply_received=False,
                            
                            # Contact information
                            contact_email=contact_info.get('email') if contact_info else None,
                            contact_name=contact_info.get('name') if contact_info else None,
                            contact_phone=contact_info.get('contact_phone') if contact_info else None,
                            website=enriched_data.get('website'),
                            contact_source=contact_info.get('source') if contact_info else None,
                            contact_source_url=contact_info.get('source_url') if contact_info else None,
                            contact_email_confidence=contact_info.get('contact_email_confidence', 0) if contact_info else 0,
                            contact_verified=contact_info.get('contact_verified', False) if contact_info else False,
                            verification_notes=contact_info.get('verification_notes') if contact_info else None,
                            verification_flags=contact_info.get('verification_flags') if contact_info else None,
                            
                            # Basic building info
                            property_manager=enriched_data.get('property_manager'),
                            number_of_units=enriched_data.get('number_of_units'),
                            year_built=enriched_data.get('year_built'),
                            square_footage=enriched_data.get('square_footage'),
                            
                            # Detailed rental information
                            is_coop=enriched_data.get('is_coop', False),
                            is_mixed_use=enriched_data.get('is_mixed_use', False),
                            total_apartments=enriched_data.get('total_apartments'),
                            two_bedroom_apartments=enriched_data.get('two_bedroom_apartments'),
                            recent_2br_rent=enriched_data.get('recent_2br_rent'),
                            rent_range_2br=enriched_data.get('rent_range_2br'),
                            has_laundry=enriched_data.get('has_laundry', False),
                            laundry_type=enriched_data.get('laundry_type'),
                            amenities=enriched_data.get('amenities'),
                            pet_policy=enriched_data.get('pet_policy'),
                            building_style=enriched_data.get('building_style'),
                            management_company=enriched_data.get('management_company'),
                            contact_info=json.dumps(contact_info) if contact_info else None,
                            recent_availability=enriched_data.get('recent_availability', False),
                            rental_notes=enriched_data.get('rental_notes'),
                            neighborhood=enriched_data.get('neighborhood'),
                            stories=enriched_data.get('stories')
                        )
                        
                        # Save additional contact sources if found
                        if contact_info and contact_info.get('additional_sources'):
                            for source in contact_info['additional_sources']:
                                contact_source = ContactSource(
                                    building_id=building.id,
                                    source_type=source.get('source_type', 'unknown'),
                                    source_url=source.get('source_url'),
                                    confidence_score=source.get('confidence_score', 0)
                                )
                                db.add(contact_source)
                        
                        db.add(building)
                        all_buildings.append(building)
                        
                    except Exception as e:
                        print(f"Error processing building {building_data.get('address')}: {str(e)}")
                        continue
            
            # Commit all buildings to database
            if all_buildings:
                db.commit()
                print(f"\n✅ Successfully processed {len(all_buildings)} buildings")
                print(f"  - Buildings with contact info: {sum(1 for b in all_buildings if b.contact_email or b.contact_name or b.contact_phone)}")
                print(f"  - Buildings with email: {sum(1 for b in all_buildings if b.contact_email)}")
                print(f"  - Buildings with phone: {sum(1 for b in all_buildings if b.contact_phone)}")
                if duplicates_found > 0:
                    print(f"  - Skipped {duplicates_found} duplicate buildings")
            else:
                print("No new buildings were processed")
            
            return all_buildings
            
        except Exception as e:
            print(f"Error in building pipeline: {str(e)}")
            db.rollback()
            raise e
    
    async def process_approved_building(self, building_id: int, db: Session):
        """
        Process an approved building through the contact finding and email sending pipeline.
        
        Args:
            building_id: ID of the approved building
            db: Database session
        """
        try:
            # Get the building
            building = db.query(Building).filter(Building.id == building_id).first()
            if not building:
                raise Exception(f"Building with ID {building_id} not found")
            
            print(f"Processing approved building: {building.address}")
            
            # Step 1: Find contact information with emphasis on building manager/realtor
            contact_info = await self.contact_finder.find_contacts(building.get('address'))
            
            if contact_info:
                # Update building with contact information
                building.contact_email = contact_info.get('email')
                building.contact_name = contact_info.get('name')
                building.property_manager = contact_info.get('title') or contact_info.get('property_manager')
                building.contact_source = contact_info.get('source')
                building.contact_source_url = contact_info.get('source_url')
                building.contact_email_confidence = contact_info.get('contact_email_confidence')
                building.contact_verified = contact_info.get('contact_verified', False)
                building.verification_notes = contact_info.get('verification_notes')
                building.verification_flags = contact_info.get('verification_flags')
                
                # Store additional contact sources if found
                if isinstance(contact_info.get('additional_sources'), list):
                    for source in contact_info['additional_sources']:
                        contact_source = ContactSource(
                            building_id=building.id,
                            source_type=source.get('source_type', 'unknown'),
                            source_url=source.get('source_url'),
                            confidence_score=source.get('confidence_score', 0)
                        )
                        db.add(contact_source)
                
                db.commit()
                print(f"Found contact: {building.contact_email}")
            else:
                print(f"No contact found for building: {building.address}")
                return
            
        except Exception as e:
            print(f"Error processing approved building: {str(e)}")
            db.rollback()
            raise e
    
    def process_bounding_boxes_sync(self, bounding_boxes: List[dict], db: Session):
        """Synchronous wrapper for async bounding box processing."""
        return asyncio.run(self.process_bounding_boxes(bounding_boxes, db))
    
    def process_approved_building_sync(self, building_id: int, db: Session):
        """Synchronous wrapper for async approved building processing."""
        return asyncio.run(self.process_approved_building(building_id, db)) 