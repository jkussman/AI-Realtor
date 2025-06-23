"""
Autonomous AI agent for finding building contacts in NYC.
Uses Puppeteer for web scraping and automation.
"""

import asyncio
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContactFinder:
    """Autonomous agent for finding building contacts in NYC."""
    
    def __init__(self, browser=None, context=None, page=None):
        """Initialize the contact finder."""
        self.browser = browser
        self.context = context
        self.page = page
        self.cache = {}  # Simple in-memory cache
        self._playwright = None
        
    async def __aenter__(self):
        """Set up browser context if not provided."""
        if not self.browser:
            try:
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            except Exception as e:
                logger.error(f"Failed to initialize browser: {str(e)}")
                return self
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser context if we created it."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.error(f"Error stopping playwright: {str(e)}")
            
    async def find_contacts(self, address: str) -> Dict:
        logger.info(f"ContactFinder.find_contacts called with address: {address}")
        try:
            # Check cache first
            if address in self.cache:
                logger.info(f"Using cached results for {address}")
                return self.cache[address]
            
            # If browser is not initialized, return empty result
            if not self.page:
                logger.warning("Browser not initialized, skipping contact finding")
                return self._create_empty_result(address)
            
            # Step 1: Get owner/manager from JustFix
            owner_info = await self._get_justfix_info(address)
            if not owner_info:
                return self._create_empty_result(address)
                
            # Step 2: Search for contact info
            contact_info = await self._search_contact_info(owner_info)
            
            # Step 3: Scrape website for emails
            if contact_info.get('website'):
                email_info = await self._scrape_website_emails(contact_info['website'])
                contact_info.update(email_info)
            
            # Cache results
            self.cache[address] = contact_info
            logger.info(f"ContactFinder.find_contacts returning: {contact_info}")
            return contact_info
            
        except Exception as e:
            logger.error(f"Error finding contacts for {address}: {str(e)}")
            return self._create_empty_result(address)
            
    async def _get_justfix_info(self, address: str) -> Optional[Dict]:
        """Get property owner/manager info from JustFix."""
        try:
            # Navigate to JustFix
            await self.page.goto('https://whoownswhat.justfix.org', wait_until='networkidle')
            
            # Wait for search input and enter address
            search_input = await self.page.wait_for_selector('input[type="search"], input[placeholder*="search"], input[placeholder*="address"]', timeout=10000)
            if not search_input:
                logger.error("Could not find search input on JustFix page")
                return None
                
            await search_input.fill(address)
            await search_input.press('Enter')
            
            # Wait for results with multiple possible selectors
            try:
                await self.page.wait_for_selector('.property-info, .search-results, .result-item', timeout=10000)
            except Exception as e:
                logger.error(f"Timeout waiting for JustFix results: {str(e)}")
                return None
            
            # Extract owner/manager info with multiple possible selectors
            owner_info = await self.page.evaluate('''() => {
                const selectors = {
                    owner: ['.owner-name', '.owner', '.property-owner', '[data-testid="owner-name"]'],
                    manager: ['.manager-name', '.manager', '.property-manager', '[data-testid="manager-name"]']
                };
                
                const getText = (selectors) => {
                    for (const selector of selectors) {
                        const element = document.querySelector(selector);
                        if (element) return element.textContent.trim();
                    }
                    return null;
                };
                
                return {
                    owner: getText(selectors.owner),
                    manager: getText(selectors.manager)
                };
            }''')
            
            if not owner_info.get('owner') and not owner_info.get('manager'):
                logger.warning("No owner or manager information found on JustFix page")
                return None
                
            return owner_info
            
        except Exception as e:
            logger.error(f"Error getting JustFix info: {str(e)}")
            return None
            
    async def _search_contact_info(self, owner_info: Dict) -> Dict:
        """Search for contact information using Google."""
        try:
            # Search for owner/manager
            search_term = f'"{owner_info["owner"] or owner_info["manager"]} property management NYC email"'
            await self.page.goto('https://www.google.com')
            await self.page.fill('input[name="q"]', search_term)
            await self.page.press('input[name="q"]', 'Enter')
            
            # Wait for results and find relevant link
            await self.page.wait_for_selector('div.g')
            website_url = await self._find_relevant_website()
            
            return {
                'manager_name': owner_info.get('manager') or owner_info.get('owner'),
                'manager_website': website_url
            }
            
        except Exception as e:
            logger.error(f"Error searching contact info: {str(e)}")
            return {'manager_name': owner_info.get('manager') or owner_info.get('owner')}
            
    async def _find_relevant_website(self) -> Optional[str]:
        """Find a relevant website from Google search results."""
        try:
            # Get all search results
            results = await self.page.evaluate('''() => {
                const results = [];
                document.querySelectorAll('div.g').forEach(div => {
                    const link = div.querySelector('a');
                    if (link) {
                        results.push({
                            url: link.href,
                            title: link.textContent,
                            snippet: div.querySelector('.VwiC3b')?.textContent
                        });
                    }
                });
                return results;
            }''')
            
            # Filter and rank results
            for result in results:
                url = result['url']
                domain = urlparse(url).netloc.lower()
                
                # Skip common spam/aggregator domains
                if any(x in domain for x in ['yelp.com', 'facebook.com', 'linkedin.com', 'yellowpages.com']):
                    continue
                    
                # Check if domain matches company name
                if self._is_relevant_domain(domain, result['title']):
                    return url
                    
            # If no perfect match, return first non-spam result
            for result in results:
                url = result['url']
                domain = urlparse(url).netloc.lower()
                if not any(x in domain for x in ['yelp.com', 'facebook.com', 'linkedin.com', 'yellowpages.com']):
                    return url
                    
            return None
            
        except Exception as e:
            logger.error(f"Error finding relevant website: {str(e)}")
            return None
            
    async def _scrape_website_emails(self, website_url: str) -> Dict:
        """Scrape emails and contact form from website."""
        try:
            # Visit website
            await self.page.goto(website_url)
            
            # Find and visit contact/leasing pages
            contact_pages = await self._find_contact_pages()
            emails = set()
            contact_form = None
            
            for page_url in contact_pages:
                await self.page.goto(page_url)
                
                # Extract emails
                page_emails = await self._extract_emails()
                emails.update(page_emails)
                
                # Look for contact form
                if not contact_form:
                    contact_form = await self._find_contact_form()
            
            # Prioritize emails
            prioritized_email = self._prioritize_emails(emails, website_url)
            
            return {
                'contact_email': prioritized_email,
                'contact_form': contact_form
            }
            
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
            return {}
            
    async def _find_contact_pages(self) -> List[str]:
        """Find contact/leasing/about pages on the website."""
        try:
            # Look for common contact page links
            contact_links = await self.page.evaluate('''() => {
                const links = [];
                const keywords = ['contact', 'leasing', 'about', 'rent'];
                document.querySelectorAll('a').forEach(a => {
                    const text = a.textContent.toLowerCase();
                    const href = a.href;
                    if (keywords.some(k => text.includes(k)) && href) {
                        links.push(href);
                    }
                });
                return links;
            }''')
            
            return list(set(contact_links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error finding contact pages: {str(e)}")
            return []
            
    async def _extract_emails(self) -> set:
        """Extract email addresses from the current page."""
        try:
            # Get page content
            content = await self.page.content()
            
            # Find all email addresses
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            emails = set(re.findall(email_pattern, content))
            
            return emails
            
        except Exception as e:
            logger.error(f"Error extracting emails: {str(e)}")
            return set()
            
    async def _find_contact_form(self) -> Optional[str]:
        """Find contact form URL on the current page."""
        try:
            # Look for common contact form patterns
            form_url = await self.page.evaluate('''() => {
                const keywords = ['contact', 'message', 'inquiry'];
                for (const a of document.querySelectorAll('a')) {
                    const text = a.textContent.toLowerCase();
                    const href = a.href;
                    if (keywords.some(k => text.includes(k)) && href) {
                        return href;
                    }
                }
                return null;
            }''')
            
            return form_url
            
        except Exception as e:
            logger.error(f"Error finding contact form: {str(e)}")
            return None
            
    def _prioritize_emails(self, emails: set, website_url: str) -> Optional[str]:
        """Prioritize email addresses based on relevance."""
        if not emails:
            return None
            
        # Get website domain
        domain = urlparse(website_url).netloc.lower()
        
        # First priority: leasing emails with company domain
        for email in emails:
            if any(x in email.lower() for x in ['leasing', 'rentals']) and domain in email.lower():
                return email
                
        # Second priority: any email with company domain
        for email in emails:
            if domain in email.lower():
                return email
                
        # Third priority: leasing emails
        for email in emails:
            if any(x in email.lower() for x in ['leasing', 'rentals']):
                return email
                
        # Last resort: any email
        return next(iter(emails))
        
    def _is_relevant_domain(self, domain: str, title: str) -> bool:
        """Check if a domain is relevant to the company."""
        # Remove common TLDs and www
        domain = domain.replace('www.', '').split('.')[0]
        title = title.lower()
        
        # Check if domain appears in title
        return domain in title
        
    def _create_empty_result(self, address: str) -> Dict:
        """Create an empty result dictionary."""
        return {
            'address': address,
            'email': None,
            'name': None,
            'phone': None,
            'title': None,
            'source': None,
            'confidence': None
        } 