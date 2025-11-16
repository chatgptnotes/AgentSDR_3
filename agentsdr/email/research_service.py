"""
Sender Research Service
InboxAI - Lindy AI-like Email Automation Platform
"""

import os
import re
import requests
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup


class ResearchService:
    """Service for researching email senders"""

    def __init__(self):
        """Initialize research service"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def research_sender(
        self,
        email_address: str,
        deep_research: bool = False
    ) -> Dict[str, Any]:
        """
        Research an email sender

        Args:
            email_address: Email address to research
            deep_research: Whether to perform deep research

        Returns:
            Research data dictionary
        """
        research_data = {
            "email_address": email_address,
            "full_name": None,
            "company": None,
            "job_title": None,
            "linkedin_url": None,
            "twitter_url": None,
            "website": None,
            "bio": None,
            "location": None,
            "social_profiles": {},
            "company_info": {},
            "research_data": {},
            "research_source": "web_search"
        }

        try:
            # Extract domain from email
            domain = email_address.split('@')[1] if '@' in email_address else None

            # Research company from domain
            if domain:
                company_info = self._research_company(domain)
                research_data["company"] = company_info.get("name")
                research_data["website"] = company_info.get("website")
                research_data["company_info"] = company_info

            # Search for LinkedIn profile
            linkedin_url = self._search_linkedin(email_address)
            if linkedin_url:
                research_data["linkedin_url"] = linkedin_url

                # If deep research, scrape LinkedIn (mock for now)
                if deep_research:
                    linkedin_data = self._scrape_linkedin(linkedin_url)
                    research_data["full_name"] = linkedin_data.get("name")
                    research_data["job_title"] = linkedin_data.get("title")
                    research_data["bio"] = linkedin_data.get("bio")
                    research_data["location"] = linkedin_data.get("location")

            # Search for Twitter profile
            twitter_url = self._search_twitter(email_address)
            if twitter_url:
                research_data["twitter_url"] = twitter_url

            # Search for personal website/blog
            website = self._search_personal_website(email_address)
            if website:
                research_data["website"] = website

            # Aggregate social profiles
            social_profiles = {}
            if linkedin_url:
                social_profiles["linkedin"] = linkedin_url
            if twitter_url:
                social_profiles["twitter"] = twitter_url
            research_data["social_profiles"] = social_profiles

            return research_data

        except Exception as e:
            print(f"Error researching sender {email_address}: {e}")
            return research_data

    def _research_company(self, domain: str) -> Dict[str, Any]:
        """
        Research company from domain

        Args:
            domain: Company domain

        Returns:
            Company information
        """
        company_info = {
            "name": None,
            "website": f"https://{domain}",
            "description": None,
            "industry": None,
            "size": None
        }

        try:
            # Try to fetch company website
            response = requests.get(
                f"https://{domain}",
                headers=self.headers,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Try to extract company name from title
                title = soup.find('title')
                if title:
                    company_info["name"] = title.get_text().strip()

                # Try to extract description from meta tags
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    company_info["description"] = meta_desc.get('content', '').strip()

                # Try to extract from Open Graph tags
                og_title = soup.find('meta', attrs={'property': 'og:title'})
                if og_title:
                    company_info["name"] = og_title.get('content', '').strip()

                og_desc = soup.find('meta', attrs={'property': 'og:description'})
                if og_desc:
                    company_info["description"] = og_desc.get('content', '').strip()

        except Exception as e:
            print(f"Error researching company {domain}: {e}")

        return company_info

    def _search_linkedin(self, email_address: str) -> Optional[str]:
        """
        Search for LinkedIn profile

        Args:
            email_address: Email address

        Returns:
            LinkedIn URL if found
        """
        try:
            # Extract name from email if possible
            name_part = email_address.split('@')[0]
            # Clean up common patterns
            name_part = re.sub(r'[._-]', ' ', name_part)

            # Google search for LinkedIn profile (mock implementation)
            search_query = f"{name_part} site:linkedin.com"
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"

            # In production, would use proper LinkedIn API or web scraping
            # For now, return mock data
            # This would require LinkedIn API access or careful web scraping

            return None  # Placeholder - would implement actual search

        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
            return None

    def _scrape_linkedin(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape LinkedIn profile (mock implementation)

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            Profile data
        """
        # Note: Actual LinkedIn scraping requires authentication
        # and may violate LinkedIn's terms of service
        # This is a mock implementation

        profile_data = {
            "name": None,
            "title": None,
            "bio": None,
            "location": None,
            "company": None
        }

        # In production, would use:
        # 1. LinkedIn Official API (requires partnership)
        # 2. Third-party enrichment services (Clearbit, Hunter.io, etc.)
        # 3. Careful web scraping with authentication

        return profile_data

    def _search_twitter(self, email_address: str) -> Optional[str]:
        """
        Search for Twitter profile

        Args:
            email_address: Email address

        Returns:
            Twitter URL if found
        """
        try:
            # Extract name from email
            name_part = email_address.split('@')[0]
            name_part = re.sub(r'[._-]', ' ', name_part)

            # Search for Twitter profile (mock implementation)
            # In production, would use Twitter API or search

            return None  # Placeholder

        except Exception as e:
            print(f"Error searching Twitter: {e}")
            return None

    def _search_personal_website(self, email_address: str) -> Optional[str]:
        """
        Search for personal website

        Args:
            email_address: Email address

        Returns:
            Website URL if found
        """
        try:
            # Extract name from email
            name_part = email_address.split('@')[0]

            # Search for personal website (mock implementation)
            # Would use Google Custom Search API or similar

            return None  # Placeholder

        except Exception as e:
            print(f"Error searching for website: {e}")
            return None

    def enrich_with_clearbit(self, email_address: str) -> Dict[str, Any]:
        """
        Enrich email data using Clearbit API (if available)

        Args:
            email_address: Email address

        Returns:
            Enriched data
        """
        clearbit_api_key = os.getenv('CLEARBIT_API_KEY')

        if not clearbit_api_key:
            return {}

        try:
            # Clearbit Enrichment API
            response = requests.get(
                f"https://person.clearbit.com/v2/combined/find?email={email_address}",
                headers={'Authorization': f'Bearer {clearbit_api_key}'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                person = data.get('person', {})
                company = data.get('company', {})

                return {
                    "full_name": person.get('name', {}).get('fullName'),
                    "job_title": person.get('employment', {}).get('title'),
                    "company": company.get('name'),
                    "linkedin_url": person.get('linkedin', {}).get('handle'),
                    "twitter_url": person.get('twitter', {}).get('handle'),
                    "bio": person.get('bio'),
                    "location": person.get('location'),
                    "company_info": {
                        "name": company.get('name'),
                        "domain": company.get('domain'),
                        "description": company.get('description'),
                        "industry": company.get('category', {}).get('industry'),
                        "size": company.get('metrics', {}).get('employees')
                    }
                }

        except Exception as e:
            print(f"Error enriching with Clearbit: {e}")

        return {}

    def enrich_with_hunter(self, email_address: str) -> Dict[str, Any]:
        """
        Enrich email data using Hunter.io API (if available)

        Args:
            email_address: Email address

        Returns:
            Enriched data
        """
        hunter_api_key = os.getenv('HUNTER_API_KEY')

        if not hunter_api_key:
            return {}

        try:
            # Hunter Email Verifier API
            response = requests.get(
                f"https://api.hunter.io/v2/email-verifier",
                params={
                    'email': email_address,
                    'api_key': hunter_api_key
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json().get('data', {})

                return {
                    "email_valid": data.get('status') == 'valid',
                    "full_name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                    "linkedin_url": data.get('linkedin'),
                    "twitter_url": data.get('twitter'),
                    "sources": data.get('sources', [])
                }

        except Exception as e:
            print(f"Error enriching with Hunter: {e}")

        return {}
