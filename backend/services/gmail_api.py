"""
Gmail API service for sending emails and managing OAuth2 authentication.
"""

import os
import pickle
import base64
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailService:
    """
    Service for Gmail API operations including sending emails and checking for replies.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self):
        self.credentials_file = 'gmail_credentials.json'  # OAuth2 credentials file
        self.token_file = 'gmail_token.pickle'  # Stored token file
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail API service with authentication."""
        try:
            creds = self._get_credentials()
            if creds:
                self.service = build('gmail', 'v1', credentials=creds)
                print("Gmail service initialized successfully")
            else:
                print("Failed to initialize Gmail service - no valid credentials")
        except Exception as e:
            print(f"Error initializing Gmail service: {e}")
            self.service = None
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid Gmail API credentials."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds and os.path.exists(self.credentials_file):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return None
            
            # Save the credentials for the next run
            if creds:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
        
        return creds
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            from_email: Sender email (optional, uses authenticated account)
            
        Returns:
            Dictionary with success status and message details
        """
        if not self.service:
            return {
                'success': False,
                'error': 'Gmail service not initialized'
            }
        
        try:
            # Create message
            message = self._create_message(to_email, subject, body, from_email)
            
            # Send message
            result = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            return {
                'success': True,
                'message_id': result['id'],
                'thread_id': result.get('threadId')
            }
            
        except HttpError as error:
            print(f"Gmail API error: {error}")
            return {
                'success': False,
                'error': f'Gmail API error: {error}'
            }
        except Exception as e:
            print(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_message(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        from_email: Optional[str] = None
    ) -> Dict[str, str]:
        """Create a message for Gmail API."""
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        if from_email:
            message['from'] = from_email
        
        # Add body
        msg_body = MIMEText(body, 'plain')
        message.attach(msg_body)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        return {'raw': raw_message}
    
    def check_for_replies(self, contact_email: str) -> bool:
        """
        Check if there are any replies from a specific email address.
        
        Args:
            contact_email: Email address to check for replies from
            
        Returns:
            True if replies found, False otherwise
        """
        if not self.service:
            print("Gmail service not initialized")
            return False
        
        try:
            # Search for messages from the contact email
            query = f'from:{contact_email}'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            if messages:
                print(f"Found {len(messages)} messages from {contact_email}")
                return True
            else:
                return False
                
        except HttpError as error:
            print(f"Error checking for replies: {error}")
            return False
        except Exception as e:
            print(f"Error checking for replies: {e}")
            return False
    
    def get_recent_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent emails from inbox.
        
        Args:
            max_results: Maximum number of emails to retrieve
            
        Returns:
            List of email data dictionaries
        """
        if not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_data = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Extract email data
                headers = msg['payload'].get('headers', [])
                email_info = {
                    'id': message['id'],
                    'thread_id': msg.get('threadId'),
                    'snippet': msg.get('snippet', ''),
                }
                
                # Extract headers
                for header in headers:
                    name = header['name'].lower()
                    if name in ['from', 'to', 'subject', 'date']:
                        email_info[name] = header['value']
                
                email_data.append(email_info)
            
            return email_data
            
        except HttpError as error:
            print(f"Error getting recent emails: {error}")
            return []
        except Exception as e:
            print(f"Error getting recent emails: {e}")
            return []
    
    def setup_oauth_credentials(self) -> Dict[str, Any]:
        """
        Setup OAuth2 credentials for Gmail API.
        This should be run once to authenticate the application.
        
        Returns:
            Dictionary with setup status
        """
        try:
            if not os.path.exists(self.credentials_file):
                return {
                    'success': False,
                    'error': f'Credentials file {self.credentials_file} not found. '
                           'Please download it from Google Cloud Console.'
                }
            
            # Initialize OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.SCOPES
            )
            
            # Run local server for authentication
            creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            # Test the service
            self._initialize_service()
            
            if self.service:
                return {
                    'success': True,
                    'message': 'OAuth2 credentials setup successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to initialize service after OAuth setup'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error setting up OAuth credentials: {str(e)}'
            }
    
    def is_authenticated(self) -> bool:
        """Check if Gmail service is properly authenticated."""
        return self.service is not None 