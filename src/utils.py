import json
import os
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Save data as JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved data to {filepath}")

def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_campaign_id() -> str:
    """Generate unique campaign ID"""
    return f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def format_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().isoformat()

def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filename"""
    return "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]