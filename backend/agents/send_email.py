"""
Agent for sending emails to property contacts via Gmail API.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os

from services.gmail_api import GmailService
from db.models import EmailLog


class EmailSender:
    """
    Agent responsible for sending emails to property contacts and logging them.
    """
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.from_email = os.getenv("FROM_EMAIL")
        self.from_name = os.getenv("FROM_NAME", "AI Realtor")
    
    async def send_email_to_contact(
        self, 
        contact_email: str, 
        contact_name: Optional[str], 
        building, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Send an email to a property contact and log it.
        
        Args:
            contact_email: Email address of the contact
            contact_name: Name of the contact (optional)
            building: Building object from database
            db: Database session
            
        Returns:
            Dictionary with success status and details
        """
        try:
            print(f"Sending email to {contact_email} for building {building.address}")
            
            # Generate email content
            email_content = self._generate_email_content(contact_name, building)
            
            # Send email via Gmail API
            email_result = await self.gmail_service.send_email(
                to_email=contact_email,
                subject=email_content['subject'],
                body=email_content['body']
            )
            
            # Log email to database
            email_log = EmailLog(
                building_id=building.id,
                subject=email_content['subject'],
                body=email_content['body'],
                sent_at=datetime.utcnow(),
                status='sent' if email_result['success'] else 'failed',
                gmail_message_id=email_result.get('message_id'),
                gmail_thread_id=email_result.get('thread_id')
            )
            
            db.add(email_log)
            db.commit()
            
            if email_result['success']:
                print(f"Email sent successfully to {contact_email}")
                return {
                    'success': True,
                    'message_id': email_result.get('message_id'),
                    'email_log_id': email_log.id
                }
            else:
                print(f"Failed to send email: {email_result.get('error')}")
                return {
                    'success': False,
                    'error': email_result.get('error'),
                    'email_log_id': email_log.id
                }
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_email_content(self, contact_name: Optional[str], building) -> Dict[str, str]:
        """
        Generate email subject and body content.
        """
        # Personalize greeting
        if contact_name:
            greeting = f"Dear {contact_name},"
        else:
            greeting = "Dear Property Manager,"
        
        # Create subject line
        subject = f"Investment Inquiry for {building.address}"
        
        # Create email body
        body = f"""{greeting}

I hope this email finds you well. My name is {self.from_name}, and I am a real estate investor actively looking for investment opportunities in New York City.

I came across the property at {building.address} and I'm very interested in learning more about potential investment opportunities related to this building.

Property Details:
- Address: {building.address}
- Building Type: {building.building_type or 'Residential Apartment Building'}
{f"- Building Name: {building.name}" if building.name else ""}
{f"- Estimated Units: {building.number_of_units}" if building.number_of_units else ""}

I am particularly interested in:
• Purchasing individual units or the entire building
• Off-market opportunities
• Buildings with value-add potential
• Long-term investment partnerships

I work with qualified investors and have access to capital for quick closings. I would appreciate the opportunity to discuss any current or upcoming opportunities you might have.

Would you be available for a brief phone call this week to discuss potential opportunities? I'm flexible with timing and can work around your schedule.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{self.from_name}
{self.from_email}

P.S. If you know of other buildings or opportunities in the area, I would be very interested in hearing about those as well.
"""
        
        return {
            'subject': subject,
            'body': body
        }
    
    def _generate_follow_up_email(self, contact_name: Optional[str], building, days_since_first: int) -> Dict[str, str]:
        """
        Generate follow-up email content.
        """
        if contact_name:
            greeting = f"Dear {contact_name},"
        else:
            greeting = "Dear Property Manager,"
        
        subject = f"Re: Investment Inquiry for {building.address}"
        
        body = f"""{greeting}

I hope you're doing well. I wanted to follow up on my email from {days_since_first} days ago regarding investment opportunities at {building.address}.

I understand you're likely very busy, but I wanted to reiterate my strong interest in this property and any other opportunities you might have available.

As a reminder, I am:
• A serious real estate investor with access to capital
• Looking for both on-market and off-market opportunities
• Able to close quickly with minimal contingencies
• Interested in building long-term relationships with property managers

If now isn't the right time, I completely understand. However, I would appreciate it if you could keep me in mind for future opportunities.

Would a brief 5-10 minute phone call work better for you? I'm happy to work around your schedule.

Thank you again for your time.

Best regards,
{self.from_name}
{self.from_email}
"""
        
        return {
            'subject': subject,
            'body': body
        }
    
    async def send_follow_up_email(
        self, 
        building, 
        days_since_first: int, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a follow-up email for a building.
        
        Args:
            building: Building object from database
            days_since_first: Number of days since first email
            db: Database session
            
        Returns:
            Dictionary with success status and details
        """
        if not building.contact_email:
            return {'success': False, 'error': 'No contact email available'}
        
        try:
            # Generate follow-up content
            email_content = self._generate_follow_up_email(
                building.contact_name, 
                building, 
                days_since_first
            )
            
            # Send email
            result = await self.send_email_to_contact(
                contact_email=building.contact_email,
                contact_name=building.contact_name,
                building=building,
                db=db
            )
            
            return result
            
        except Exception as e:
            print(f"Error sending follow-up email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_email_content(self, content: Dict[str, str]) -> bool:
        """
        Validate email content before sending.
        """
        required_fields = ['subject', 'body']
        
        for field in required_fields:
            if not content.get(field):
                return False
            
            if len(content[field].strip()) == 0:
                return False
        
        # Check for reasonable length
        if len(content['subject']) > 200:
            return False
            
        if len(content['body']) > 10000:
            return False
        
        return True 