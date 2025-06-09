"""
Main building pipeline that orchestrates all agent steps.
"""

import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json

from .get_buildings import BuildingFinder
from .enrich_building import BuildingEnricher
from .find_contact import ContactFinder
# Commenting out email sender for now
# from .send_email import EmailSender
from db.models import Building
from langchain_openai import OpenAI


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
            model_name="gpt-4-turbo-preview"
        )
        
        # Initialize pipeline components
        self.building_finder = BuildingFinder(google_api_key)
        self.building_enricher = BuildingEnricher(llm=self.llm)
        self.contact_finder = ContactFinder(llm=self.llm)
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
                        # Find contact information
                        contact_info = await self.contact_finder.find_contact_for_building(enriched)
                        if contact_info:
                            enriched.update(contact_info)
                        
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
            
            for bbox in bounding_boxes:
                print(f"Processing bounding box: {bbox}")
                
                # Step 1: Find buildings in the bounding box
                buildings = await self.building_finder.get_buildings_from_bbox(bbox)
                
                for building_data in buildings:
                    try:
                        # Step 2: Enrich building data
                        enriched_data = await self.building_enricher.enrich_building(building_data)
                        
                        # Step 3: Save to database
                        building = Building(
                            name=enriched_data.get('name'),
                            address=enriched_data['address'],
                            latitude=str(enriched_data.get('latitude')) if enriched_data.get('latitude') else None,
                            longitude=str(enriched_data.get('longitude')) if enriched_data.get('longitude') else None,
                            building_type=enriched_data.get('building_type', 'residential_apartment'),
                            bounding_box=json.dumps(bbox),
                            approved=False,
                            email_sent=False,
                            reply_received=False,
                            
                            # Basic building info
                            property_manager=enriched_data.get('property_manager'),
                            number_of_units=enriched_data.get('estimated_units'),
                            year_built=enriched_data.get('year_built'),
                            
                            # Detailed rental information
                            is_coop=enriched_data.get('is_coop', False),
                            is_mixed_use=enriched_data.get('is_mixed_use', False),
                            total_apartments=enriched_data.get('total_apartments'),
                            two_bedroom_apartments=enriched_data.get('two_bedroom_apartments'),
                            recent_2br_rent=enriched_data.get('recent_2br_rent'),
                            rent_range_2br=enriched_data.get('rent_range_2br'),
                            has_laundry=enriched_data.get('has_laundry', False),
                            laundry_type=enriched_data.get('laundry_type'),
                            amenities=json.dumps(enriched_data.get('amenities', [])),
                            pet_policy=enriched_data.get('pet_policy'),
                            building_style=enriched_data.get('building_style'),
                            management_company=enriched_data.get('management_company'),
                            contact_info=enriched_data.get('contact_info'),
                            recent_availability=enriched_data.get('recent_availability', False),
                            rental_notes=enriched_data.get('rental_notes'),
                            neighborhood=enriched_data.get('neighborhood'),
                            stories=enriched_data.get('stories')
                        )
                        
                        db.add(building)
                        all_buildings.append(building)
                        
                    except Exception as e:
                        print(f"Error processing building {building_data.get('address')}: {str(e)}")
                        continue
            
            # Commit all buildings to database
            if all_buildings:
                db.commit()
                print(f"Successfully processed {len(all_buildings)} buildings")
            else:
                print("No buildings were processed")
            
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
            
            # Step 1: Find contact information
            if not building.contact_email:
                contact_info = await self.contact_finder.find_contact_for_building(building)
                
                if contact_info:
                    building.contact_email = contact_info.get('email')
                    building.contact_name = contact_info.get('name')
                    building.property_manager = contact_info.get('property_manager')
                    db.commit()
                    print(f"Found contact: {building.contact_email}")
                else:
                    print(f"No contact found for building: {building.address}")
                    return
            
            # Commenting out email sending for now
            # # Step 2: Send email if contact found
            # if building.contact_email and not building.email_sent:
            #     email_result = await self.email_sender.send_email_to_contact(
            #         contact_email=building.contact_email,
            #         contact_name=building.contact_name,
            #         building=building,
            #         db=db
            #     )
                
            #     if email_result['success']:
            #         building.email_sent = True
            #         db.commit()
            #         print(f"Email sent successfully to {building.contact_email}")
            #     else:
            #         print(f"Failed to send email: {email_result['error']}")
            
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