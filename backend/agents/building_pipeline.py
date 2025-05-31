"""
Main building pipeline that orchestrates all agent steps.
"""

import asyncio
from typing import List
from sqlalchemy.orm import Session

from .get_buildings import BuildingFinder
from .enrich_building import BuildingEnricher
from .find_contact import ContactFinder
from .send_email import EmailSender
from db.models import Building


class BuildingPipeline:
    """
    Main pipeline that orchestrates the building discovery and outreach process.
    """
    
    def __init__(self):
        self.building_finder = BuildingFinder()
        self.building_enricher = BuildingEnricher()
        self.contact_finder = ContactFinder()
        self.email_sender = EmailSender()
    
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
                    # Step 2: Enrich building data
                    enriched_data = await self.building_enricher.enrich_building(building_data)
                    
                    # Step 3: Save to database
                    building = Building(
                        name=enriched_data.get('name'),
                        address=enriched_data['address'],
                        building_type=enriched_data.get('building_type', 'residential_apartment'),
                        bounding_box=bbox,
                        property_manager=enriched_data.get('property_manager'),
                        number_of_units=enriched_data.get('number_of_units'),
                        year_built=enriched_data.get('year_built'),
                        square_footage=enriched_data.get('square_footage')
                    )
                    
                    db.add(building)
                    all_buildings.append(building)
            
            # Commit all buildings to database
            db.commit()
            
            print(f"Successfully processed {len(all_buildings)} buildings")
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
            
            # Step 2: Send email if contact found
            if building.contact_email and not building.email_sent:
                email_result = await self.email_sender.send_email_to_contact(
                    contact_email=building.contact_email,
                    contact_name=building.contact_name,
                    building=building,
                    db=db
                )
                
                if email_result['success']:
                    building.email_sent = True
                    db.commit()
                    print(f"Email sent successfully to {building.contact_email}")
                else:
                    print(f"Failed to send email: {email_result['error']}")
            
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