"""
Image processing service
"""
import httpx
import asyncio
from typing import Optional
from PIL import Image
from io import BytesIO
import logging
import base64

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image processing and manipulation"""
    
    async def download_image(self, image_url: str) -> bytes:
        """
        Download image from URL with timeout and retry logic
        
        Args:
            image_url: URL of the image to download
        
        Returns:
            Image bytes
        """
        from app.config import settings
        
        max_retries = 3
        timeout = settings.http_timeout
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    return response.content
            except httpx.TimeoutException:
                logger.warning(f"Image download timeout (attempt {attempt + 1}/{max_retries}): {image_url}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to download image: timeout after {timeout}s")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.RequestError as e:
                logger.warning(f"Image download error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to download image: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Failed to download image from {image_url}: {str(e)}")
                raise ValueError(f"Failed to download image: {str(e)}")
    
    def decode_base64_image(self, image_base64: str) -> bytes:
        """
        Decode base64 encoded image
        
        Args:
            image_base64: Base64 encoded image string
        
        Returns:
            Image bytes
        """
        try:
            # Remove data URL prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            return base64.b64decode(image_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {str(e)}")
            raise ValueError(f"Invalid base64 image: {str(e)}")
    
    def process_image(self, image_data: bytes, max_size: Optional[tuple] = None) -> Image.Image:
        """
        Process and validate image
        
        Args:
            image_data: Image bytes
            max_size: Optional maximum size tuple (width, height)
        
        Returns:
            PIL Image object
        """
        try:
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if max_size is specified
            if max_size:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise ValueError(f"Invalid image format: {str(e)}")
    
    def validate_image(self, image_data: bytes, max_size_mb: float = 10.0) -> bool:
        """
        Validate image size and format
        
        Args:
            image_data: Image bytes
            max_size_mb: Maximum image size in MB
        
        Returns:
            True if image is valid
        """
        # Check size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"Image size ({size_mb:.2f} MB) exceeds maximum ({max_size_mb} MB)")
        
        # Check format
        try:
            image = Image.open(BytesIO(image_data))
            image.verify()
            return True
        except Exception as e:
            raise ValueError(f"Invalid image format: {str(e)}")
