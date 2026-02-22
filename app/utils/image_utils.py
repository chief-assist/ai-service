"""
Image utility functions
"""
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional


def resize_image(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: PIL Image object
        max_size: Maximum size tuple (width, height)
    
    Returns:
        Resized image
    """
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def image_to_bytes(image: Image.Image, format: str = 'JPEG') -> bytes:
    """
    Convert PIL Image to bytes
    
    Args:
        image: PIL Image object
        format: Image format (JPEG, PNG, etc.)
    
    Returns:
        Image bytes
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """
    Convert bytes to PIL Image
    
    Args:
        image_bytes: Image bytes
    
    Returns:
        PIL Image object
    """
    return Image.open(BytesIO(image_bytes))


def get_image_size_mb(image_bytes: bytes) -> float:
    """
    Get image size in megabytes
    
    Args:
        image_bytes: Image bytes
    
    Returns:
        Size in MB
    """
    return len(image_bytes) / (1024 * 1024)
