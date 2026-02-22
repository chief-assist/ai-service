"""
Ollama AI service integration
"""
import httpx
import base64
from app.config import settings
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama AI (local models)"""
    
    def __init__(self):
        """Initialize Ollama AI client"""
        self.ollama_url = settings.ollama_url
        self.model = settings.ollama_model
        
        if not self.ollama_url or not self.model:
            logger.warning("Ollama URL or model not configured")
            self.client = None
        else:
            self.client = httpx.AsyncClient(
                base_url=self.ollama_url,
                timeout=settings.ollama_timeout
            )
            logger.info(f"Ollama AI initialized with model: {self.model} at {self.ollama_url}")
    
    def is_available(self) -> bool:
        """Check if Ollama AI is available"""
        return self.client is not None
    
    async def _check_connection(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {str(e)}")
            return False
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama AI with retry logic and timeout
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text response
        """
        if not self.is_available():
            raise RuntimeError("Ollama AI is not available. Check Ollama URL and model configuration.")
        
        max_retries = settings.ollama_max_retries
        timeout = settings.ollama_timeout
        
        for attempt in range(max_retries):
            try:
                # Check connection first
                if not await self._check_connection():
                    raise ConnectionError("Ollama server is not reachable")
                
                # Use chat API for better results
                response = await asyncio.wait_for(
                    self.client.post(
                        "/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "stream": False,
                            **kwargs
                        }
                    ),
                    timeout=timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                else:
                    raise ValueError("Empty or invalid response from Ollama")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Ollama API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Ollama API request timed out after {timeout}s after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a network/connection error that we should retry
                if any(keyword in error_msg for keyword in ['timeout', 'unavailable', 'connection', 'network', '503', '502', 'failed to connect']):
                    logger.warning(f"Ollama API connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"Failed to connect to Ollama API after {max_retries} attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Non-retryable error
                    logger.error(f"Ollama text generation failed: {str(e)}")
                    raise
    
    async def generate_with_image(self, prompt: str, image_data: bytes, **kwargs) -> str:
        """
        Generate text using Ollama AI with image input (vision models)
        
        Args:
            prompt: Text prompt for generation
            image_data: Image bytes
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text response
        """
        if not self.is_available():
            raise RuntimeError("Ollama AI is not available. Check Ollama URL and model configuration.")
        
        max_retries = settings.ollama_max_retries
        timeout = settings.ollama_timeout
        
        for attempt in range(max_retries):
            try:
                # Check connection first
                if not await self._check_connection():
                    raise ConnectionError("Ollama server is not reachable")
                
                # Convert image to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Use chat API with vision support
                # Ollama vision models expect images in the message content
                response = await asyncio.wait_for(
                    self.client.post(
                        "/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt,
                                    "images": [image_base64]
                                }
                            ],
                            "stream": False,
                            **kwargs
                        }
                    ),
                    timeout=timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                else:
                    raise ValueError("Empty or invalid response from Ollama")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Ollama API timeout with image (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Ollama API request with image timed out after {timeout}s after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a network/connection error that we should retry
                if any(keyword in error_msg for keyword in ['timeout', 'unavailable', 'connection', 'network', '503', '502', 'failed to connect']):
                    logger.warning(f"Ollama API connection error with image (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"Failed to connect to Ollama API after {max_retries} attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Non-retryable error
                    logger.error(f"Ollama image generation failed: {str(e)}")
                    raise
    
    async def generate_structured(self, prompt: str, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured response using Ollama AI
        
        Args:
            prompt: Text prompt for generation
            response_format: Expected response format/schema
        
        Returns:
            Structured response as dictionary
        """
        if not self.is_available():
            raise RuntimeError("Ollama AI is not available. Check Ollama URL and model configuration.")
        
        try:
            # Add format instruction to prompt
            format_instruction = f"\n\nReturn the response as JSON matching this structure: {response_format}"
            full_prompt = prompt + format_instruction
            
            response = await self.generate_text(full_prompt)
            
            # Parse JSON response
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {str(e)}")
            raise ValueError("Invalid JSON response from Ollama AI")
        except Exception as e:
            logger.error(f"Ollama structured generation failed: {str(e)}")
            raise
