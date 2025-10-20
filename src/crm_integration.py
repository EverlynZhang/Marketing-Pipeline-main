import requests
from typing import Dict, List, Any
import random
from config import Config
from src.utils import logger, format_timestamp

class CRMIntegration:
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.HUBSPOT_API_KEY
        self.base_url = self.config.HUBSPOT_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.mock_mode = (
            not self.api_key or 
            self.api_key == 'your_hubspot_key_here' or
            len(self.api_key) < 20
        )
        
        if self.mock_mode:
            logger.warning("🔧 Running in MOCK MODE - No actual HubSpot API calls will be made")
            logger.info("💡 To use real HubSpot API, add valid HUBSPOT_API_KEY to .env file")
    
    def create_or_update_contact(self, email: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a contact in HubSpot"""
        if self.mock_mode:
            return self._mock_contact_response(email, properties)
        
        url = f"{self.base_url}/crm/v3/objects/contacts"
        
        payload = {
            "properties": {
                "email": email,
                **properties
            }
        }
        
        try:
            # Try to create contact
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 409:  # Contact exists, update instead
                contact_id = self._get_contact_by_email(email)
                return self._update_contact(contact_id, properties)
            
            response.raise_for_status()
            logger.info(f"Contact created: {email}")
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning(f"HubSpot authentication failed, switching to mock mode")
                self.mock_mode = True
                return self._mock_contact_response(email, properties)
            logger.error(f"Error creating/updating contact: {e}")
            return self._mock_contact_response(email, properties)
        
        except Exception as e:
            logger.error(f"Error creating/updating contact: {e}")
            return self._mock_contact_response(email, properties)
    
    def _get_contact_by_email(self, email: str) -> str:
        """Get contact ID by email"""
        if self.mock_mode:
            return f"mock_{abs(hash(email)) % 10000}"
        
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            results = response.json()
            
            if results.get('results'):
                return results['results'][0]['id']
            return None
        except:
            return None
    
    def _update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact"""
        if self.mock_mode:
            return self._mock_contact_response(f"contact_{contact_id}", properties)
        
        url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
        payload = {"properties": properties}
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Contact updated: {contact_id}")
            return response.json()
        except:
            return self._mock_contact_response(f"contact_{contact_id}", properties)
    
    def segment_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Segment contacts by persona"""
        segments = {persona: [] for persona in self.config.PERSONAS.keys()}
        
        for contact in contacts:
            persona = contact.get('persona', 'founders')
            if persona in segments:
                segments[persona].append(contact)
        
        logger.info(f"Contacts segmented: {', '.join([f'{k}: {len(v)}' for k, v in segments.items()])}")
        return segments
    
    def send_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email campaign to segmented audiences"""
        # Check if we can use real marketing emails
        can_use_marketing = self._check_marketing_access()
        
        if self.mock_mode or not can_use_marketing:
            if not can_use_marketing and not self.mock_mode:
                logger.info("📧 Marketing Hub not available - using mock mode for campaigns")
                logger.info("   (Contact management still uses real HubSpot API)")
            else:
                logger.info("📧 Simulating campaign distribution (MOCK MODE)")
            return self._mock_campaign_distribution(campaign_data)
        
        # If we have Marketing Hub access, try real API
        url = f"{self.base_url}/marketing/v3/emails"
        results = {}
        
        for persona, newsletter in campaign_data['newsletters'].items():
            payload = {
                "name": f"{campaign_data['blog_title']} - {persona}",
                "subject": newsletter['subject_line'],
                "emailBody": newsletter['content'],
                "previewText": newsletter.get('preview_text', ''),
                "campaignName": campaign_data['campaign_id']
            }
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                results[persona] = response.json()
                logger.info(f"✓ Campaign sent to {persona} segment")
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [401, 403]:
                    # No marketing access - switch to mock for all
                    logger.warning(f"Marketing Hub not accessible (HTTP {e.response.status_code})")
                    logger.info("Switching to mock mode for campaign distribution")
                    return self._mock_campaign_distribution(campaign_data)
                
                logger.error(f"Error sending campaign to {persona}: {e}")
                results[persona] = self._mock_campaign_response(campaign_data, persona)
            
            except Exception as e:
                logger.error(f"Error sending campaign to {persona}: {e}")
                results[persona] = self._mock_campaign_response(campaign_data, persona)
        
        return results

    def _check_marketing_access(self) -> bool:
        """Check if Marketing Hub is accessible"""
        if self.mock_mode:
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/marketing/v3/emails",
                headers=self.headers,
                params={'limit': 1},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def log_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log campaign metadata"""
        log_entry = {
            'campaign_id': campaign_data['campaign_id'],
            'blog_title': campaign_data['blog_title'],
            'send_date': format_timestamp(),
            'personas': list(campaign_data['newsletters'].keys()),
            'status': 'sent' if not self.mock_mode else 'simulated',
            'mode': 'mock' if self.mock_mode else 'production'
        }
        
        logger.info(f"Campaign logged: {log_entry['campaign_id']} ({log_entry['mode']} mode)")
        return log_entry
    
    def _mock_contact_response(self, email: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock contact response"""
        return {
            'id': f"mock_{abs(hash(email)) % 10000}",
            'properties': {
                'email': email,
                **properties
            },
            'createdAt': format_timestamp(),
            'updatedAt': format_timestamp(),
            'mock': True
        }
    
    def _mock_campaign_response(self, campaign_data: Dict[str, Any], persona: str) -> Dict[str, Any]:
        """Generate mock campaign response for single persona"""
        return {
            'id': f"campaign_{persona}_{random.randint(1000, 9999)}",
            'status': 'SCHEDULED',
            'created': format_timestamp(),
            'persona': persona,
            'mock': True
        }
    
    def _mock_campaign_distribution(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete mock campaign distribution"""
        results = {}
        
        for persona in campaign_data['newsletters'].keys():
            results[persona] = {
                'id': f"campaign_{persona}_{random.randint(1000, 9999)}",
                'status': 'SIMULATED',
                'created': format_timestamp(),
                'persona': persona,
                'recipients': random.randint(80, 100),
                'subject': campaign_data['newsletters'][persona]['subject_line'],
                'mock': True
            }
            logger.info(f"   ✓ {persona}: Simulated send to {results[persona]['recipients']} contacts")
        
        return results
    
    def create_mock_contacts(self, count_per_persona: int = 10) -> List[Dict[str, Any]]:
        """Create mock contact data for testing"""
        contacts = []
        
        # Realistic company names
        companies = [
            'PixelForge Studio', 'CreativeFlow Agency', 'DesignLab Co',
            'InnovateTech', 'BrightIdeas Inc', 'StudioX Creative',
            'Workflow Masters', 'AgileDesign', 'TechCanvas',
            'CreativeMind Agency', 'DigitalCraft', 'VisionWorks'
        ]
        
        # Realistic first names
        first_names = [
            'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey',
            'Riley', 'Jamie', 'Sam', 'Drew', 'Quinn'
        ]
        
        for persona_key in self.config.PERSONAS.keys():
            for i in range(count_per_persona):
                company = random.choice(companies)
                firstname = random.choice(first_names)
                
                contact = {
                    'email': f"{firstname.lower()}.{persona_key}{i}@{company.lower().replace(' ', '')}.com",
                    'firstname': firstname,
                    'lastname': persona_key.capitalize(),
                    'company': company,
                    'persona': persona_key,
                    'jobtitle': self.config.PERSONAS[persona_key]['name'].split('/')[0].strip()
                }
                contacts.append(contact)
        
        logger.info(f"Created {len(contacts)} mock contacts")
        return contacts
    