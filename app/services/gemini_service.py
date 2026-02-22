"""
Gemini AI service integration
"""
import os
import google.generativeai as genai
from app.config import settings
from typing import List, Dict, Any, Optional
import logging
import asyncio
import time

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini AI client"""
        api_key = settings.google_api_key or settings.google_generative_ai_api_key
        if not api_key:
            logger.warning("Gemini API key not configured")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(settings.gemini_model)
                logger.info(f"Gemini AI initialized with model: {settings.gemini_model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {str(e)}")
                self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini AI is available"""
        return self.model is not None
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Gemini AI with retry logic and timeout
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text response
        """
        if not self.is_available():
            raise RuntimeError("Gemini AI is not available. Check API key configuration.")
        
        max_retries = settings.gemini_max_retries
        timeout = settings.gemini_timeout
        
        for attempt in range(max_retries):
            try:
                # Run in executor to handle timeout
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.model.generate_content(prompt, **kwargs)
                    ),
                    timeout=timeout
                )
                
                if response.text:
                    return response.text
                else:
                    raise ValueError("Empty response from Gemini AI")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Gemini API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Gemini API request timed out after {timeout}s after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a network/connection error that we should retry
                if any(keyword in error_msg for keyword in ['timeout', 'unavailable', 'connection', 'network', '503', '502']):
                    logger.warning(f"Gemini API connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"Failed to connect to Gemini API after {max_retries} attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Non-retryable error
                    logger.error(f"Gemini text generation failed: {str(e)}")
                    raise
    
    async def generate_with_image(self, prompt: str, image_data: bytes, **kwargs) -> str:
        """
        Generate text using Gemini AI with image input (with retry logic and timeout)
        
        Args:
            prompt: Text prompt for generation
            image_data: Image bytes
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text response
        """
        if not self.is_available():
            raise RuntimeError("Gemini AI is not available. Check API key configuration.")
        
        max_retries = settings.gemini_max_retries
        timeout = settings.gemini_timeout
        
        for attempt in range(max_retries):
            try:
                import PIL.Image
                from io import BytesIO
                
                # Convert bytes to PIL Image
                image = PIL.Image.open(BytesIO(image_data))
                
                # Run in executor to handle timeout
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.model.generate_content([prompt, image], **kwargs)
                    ),
                    timeout=timeout
                )
                
                if response.text:
                    return response.text
                else:
                    raise ValueError("Empty response from Gemini AI")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Gemini API timeout with image (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Gemini API request with image timed out after {timeout}s after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a network/connection error that we should retry
                if any(keyword in error_msg for keyword in ['timeout', 'unavailable', 'connection', 'network', '503', '502', 'failed to connect']):
                    logger.warning(f"Gemini API connection error with image (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"Failed to connect to Gemini API after {max_retries} attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Non-retryable error
                    logger.error(f"Gemini image generation failed: {str(e)}")
                    raise
    
    async def generate_structured(self, prompt: str, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured response using Gemini AI
        
        Args:
            prompt: Text prompt for generation
            response_format: Expected response format/schema
        
        Returns:
            Structured response as dictionary
        """
        if not self.is_available():
            raise RuntimeError("Gemini AI is not available. Check API key configuration.")
        
        try:
            # Add format instruction to prompt
            format_instruction = f"\n\nReturn the response as JSON matching this structure: {response_format}"
            full_prompt = prompt + format_instruction
            
            response = await self.generate_text(full_prompt)
            
            # Parse JSON response
            import json
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
            raise ValueError("Invalid JSON response from Gemini AI")
        except Exception as e:
            logger.error(f"Gemini structured generation failed: {str(e)}")
            raise
