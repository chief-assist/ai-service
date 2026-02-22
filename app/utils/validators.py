"""
Input validation utilities
"""
from typing import Optional
from urllib.parse import urlparse
import re


def validate_image_url(url: str) -> bool:
    """
    Validate image URL format
    
    Args:
        url: Image URL to validate
    
    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False


def validate_base64_image(base64_str: str) -> bool:
    """
    Validate base64 encoded image
    
    Args:
        base64_str: Base64 encoded string
    
    Returns:
        True if valid base64 image
    """
    # Remove data URL prefix if present
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    # Check if it's valid base64
    try:
        import base64
        base64.b64decode(base64_str, validate=True)
        return True
    except Exception:
        return False


def validate_ingredient_list(ingredients: list) -> bool:
    """
    Validate ingredient list
    
    Args:
        ingredients: List of ingredient names
    
    Returns:
        True if valid
    """
    if not isinstance(ingredients, list):
        return False
    
    if len(ingredients) == 0:
        return False
    
    # Check that all items are strings
    return all(isinstance(ing, str) and len(ing.strip()) > 0 for ing in ingredients)


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
    
    Returns:
        Sanitized text
    """
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Trim whitespace
    text = text.strip()
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text
