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
        """Check if Ollama server is reachable and model exists"""
        if not self.client:
            return False
        try:
            # Quick health check with short timeout
            response = await asyncio.wait_for(
                self.client.get("/api/tags"),
                timeout=3.0
            )
            if response.status_code == 200:
                # Verify the model exists
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if model exists (with or without :latest tag)
                model_found = (
                    self.model in model_names or 
                    f"{self.model}:latest" in model_names or
                    any(self.model in name for name in model_names)
                )
                if not model_found:
                    logger.warning(f"Model '{self.model}' not found in Ollama.")
                    logger.warning(f"Available models: {', '.join(model_names) if model_names else 'None'}")
                    logger.warning(f"Install it with: ollama pull {self.model}")
                    # Don't fail - let the actual request try (model might work anyway)
                    return True  # Changed to True - don't block on model check
                return True
            return False
        except httpx.ConnectError:
            logger.warning(f"Ollama connection check failed: Cannot connect to {self.ollama_url}")
            logger.warning(f"  → Make sure Ollama is running: 'ollama serve'")
            logger.warning(f"  → Or check if Ollama is on a different port")
            return False
        except httpx.TimeoutException:
            logger.debug(f"Ollama connection check timed out. Server might be slow or overloaded.")
            # Don't fail on timeout - server might just be busy
            return True  # Changed to True - let the actual request try
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {type(e).__name__}: {str(e) or 'Unknown error'}")
            # Don't fail on check errors - let the actual request try
            return True  # Changed to True - connection check is just a hint
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama AI with retry logic and timeout
        Uses /api/generate for local Ollama (more stable than /api/chat)
        
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
                # Check connection first (non-blocking - just a hint)
                # Only check on first attempt to avoid slowing down retries
                if attempt == 0:
                    try:
                        connection_ok = await asyncio.wait_for(self._check_connection(), timeout=2.0)
                        if not connection_ok:
                            logger.warning("Connection check failed, but attempting request anyway...")
                    except Exception as check_error:
                        logger.debug(f"Connection check error (non-blocking): {check_error}")
                        # Continue anyway - the actual request will tell us if it's really down
                # Don't check on retries - just try the request
                
                # Use /api/generate for local Ollama (more stable and reliable)
                # This endpoint works better with local models and handles long prompts better
                logger.debug(f"Generating text with Ollama model '{self.model}' (attempt {attempt + 1}/{max_retries})")
                
                response = await asyncio.wait_for(
                    self.client.post(
                        "/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                **kwargs.get("options", {})
                            }
                        },
                        timeout=timeout
                    ),
                    timeout=timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Handle response format
                if "response" in data:
                    return data["response"]
                elif "message" in data and "content" in data["message"]:
                    # Some models return chat-like format
                    return data["message"]["content"]
                else:
                    logger.warning(f"Unexpected response format: {list(data.keys())}")
                    # Try to extract any text from response
                    if "text" in data:
                        return data["text"]
                    raise ValueError(f"Unexpected response format from Ollama: {list(data.keys())}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Ollama API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Ollama API request timed out after {timeout}s after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                # HTTP error from Ollama
                error_details = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                logger.error(f"Ollama API HTTP error (attempt {attempt + 1}/{max_retries}): {error_details}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Ollama API returned error: {error_details}") from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.ConnectError as e:
                # Connection refused - Ollama not running
                error_msg = f"Cannot connect to Ollama at {self.ollama_url}. Is Ollama running?"
                logger.warning(f"Ollama API connection error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt == max_retries - 1:
                    raise ConnectionError(error_msg) from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.TimeoutException as e:
                # Request timeout
                error_msg = f"Request to Ollama timed out after {timeout}s"
                logger.warning(f"Ollama API timeout (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt == max_retries - 1:
                    raise TimeoutError(error_msg) from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.RequestError as e:
                # Other network/connection errors
                error_msg = f"{type(e).__name__}: {str(e) or 'Network error'}"
                if hasattr(e, 'request') and e.request:
                    error_msg += f" (URL: {e.request.url})"
                logger.warning(f"Ollama API request error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Ollama API after {max_retries} attempts: {error_msg}") from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                # Other errors - log full details
                import traceback
                error_details = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Ollama text generation failed (attempt {attempt + 1}/{max_retries}): {error_details}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Ollama text generation failed: {error_details}") from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
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
