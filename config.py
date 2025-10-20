import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # HubSpot Configuration
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
    HUBSPOT_ACCOUNT_ID = os.getenv('HUBSPOT_ACCOUNT_ID')
    HUBSPOT_BASE_URL = 'https://api.hubapi.com'
    
    # Content Configuration
    BLOG_WORD_COUNT = (400, 600)
    NEWSLETTER_WORD_COUNT = (150, 250)
    
    # Data Paths
    DATA_DIR = 'data'
    CONTENT_DIR = os.path.join(DATA_DIR, 'generated_content')
    CAMPAIGNS_DIR = os.path.join(DATA_DIR, 'campaigns')
    ANALYTICS_DIR = os.path.join(DATA_DIR, 'analytics')
    
    # Personas
    PERSONAS = {
        'founders': {
            'name': 'Founders / Decision-Makers',
            'focus': ['ROI', 'growth', 'efficiency', 'competitive advantage'],
            'tone': 'executive, data-driven, strategic'
        },
        'creatives': {
            'name': 'Creative Professionals',
            'focus': ['inspiration', 'time-saving tools', 'creativity', 'design'],
            'tone': 'inspiring, visual, innovative'
        },
        'operations': {
            'name': 'Operations Managers',
            'focus': ['workflows', 'integrations', 'reliability', 'scalability'],
            'tone': 'technical, practical, process-oriented'
        }
    }
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.CONTENT_DIR, cls.CAMPAIGNS_DIR, cls.ANALYTICS_DIR]:
            os.makedirs(directory, exist_ok=True)