"""
Text processing utilities
"""
import re
import json
from typing import Dict, Any, Optional


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object or array from text
    
    Args:
        text: Text that may contain JSON
    
    Returns:
        Parsed JSON object or None
    """
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON array
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()


def parse_ingredient_list(text: str) -> list:
    """
    Parse ingredient list from text
    
    Args:
        text: Text containing ingredient names
    
    Returns:
        List of ingredient names
    """
    # Try JSON first
    json_data = extract_json_from_text(text)
    if json_data and isinstance(json_data, list):
        return [item.get('name', item) if isinstance(item, dict) else item for item in json_data]
    
    # Fallback: extract from lines
    lines = text.split('\n')
    ingredients = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('{') and not line.startswith('['):
            # Remove bullet points, numbers, etc.
            line = re.sub(r'^[-•\d.]+\s*', '', line)
            if line:
                ingredients.append(line.split(',')[0].strip())
    
    return ingredients
