"""
Ingredient recognition service
"""
import logging
from typing import List
from fastapi import HTTPException
from app.models.schemas import IngredientRecognitionRequest, IngredientRecognitionResponse, Ingredient
from app.services.gemini_service import GeminiService
from app.services.image_service import ImageService
import time
import json

logger = logging.getLogger(__name__)


class RecognitionService:
    """Service for ingredient recognition from images"""
    
    def __init__(self):
        """Initialize recognition service"""
        self.gemini_service = GeminiService()
        self.image_service = ImageService()
    
    async def recognize_ingredients(self, request: IngredientRecognitionRequest) -> IngredientRecognitionResponse:
        """
        Recognize ingredients from image using Gemini AI
        
        Args:
            request: Ingredient recognition request
        
        Returns:
            Recognition response with identified ingredients
        """
        start_time = time.time()
        
        try:
            # Get image data
            if request.image_url:
                image_data = await self.image_service.download_image(str(request.image_url))
            elif request.image_base64:
                image_data = self.image_service.decode_base64_image(request.image_base64)
            else:
                raise ValueError("Either image_url or image_base64 must be provided")
            
            # Validate image
            self.image_service.validate_image(image_data)
            
            # Process image
            image = self.image_service.process_image(image_data, max_size=(1024, 1024))
            
            # Convert image to bytes for Gemini
            from io import BytesIO
            image_bytes = BytesIO()
            image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            
            # Create prompt for ingredient recognition
            prompt = """Identify all ingredients visible in this image. 
            Return a JSON array of ingredients with the following structure:
            [
                {
                    "name": "ingredient_name",
                    "confidence": 0.0-1.0,
                    "quantity": "detected_quantity_or_null",
                    "unit": "unit_of_measurement_or_null"
                }
            ]
            Only include ingredients you can clearly identify. Be specific with ingredient names."""
            
            # Use Gemini Vision for recognition
            response_text = await self.gemini_service.generate_with_image(
                prompt,
                image_bytes.getvalue()
            )
            
            # Parse response
            ingredients = self._parse_ingredients_response(response_text)
            
            processing_time = time.time() - start_time
            
            return IngredientRecognitionResponse(
                ingredients=ingredients,
                processing_time=round(processing_time, 2)
            )
            
        except TimeoutError as e:
            logger.error(f"Ingredient recognition timeout: {str(e)}")
            raise HTTPException(
                status_code=504,
                detail=f"Request timed out. The AI service took too long to respond. Please try again or use a smaller image."
            ) from e
        except ConnectionError as e:
            logger.error(f"Ingredient recognition connection error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Unable to connect to AI service. Please check your internet connection and try again."
            ) from e
        except ValueError as e:
            logger.error(f"Ingredient recognition validation error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            ) from e
        except Exception as e:
            logger.error(f"Ingredient recognition failed: {str(e)}")
            # Provide user-friendly error message
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="AI service authentication failed. Please check API key configuration."
                ) from e
            elif "timeout" in error_msg:
                raise HTTPException(
                    status_code=504,
                    detail="Request timed out. Please try again with a smaller image or check your connection."
                ) from e
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Recognition failed: {str(e)}"
                ) from e
    
    def _parse_ingredients_response(self, response_text: str) -> List[Ingredient]:
        """
        Parse Gemini response into ingredient list
        
        Args:
            response_text: Raw response from Gemini AI
        
        Returns:
            List of Ingredient objects
        """
        try:
            # Try to extract JSON from response
            # Gemini might return text with JSON, so we need to extract it
            import re
            
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                ingredients_data = json.loads(json_str)
            else:
                # Try parsing the entire response as JSON
                ingredients_data = json.loads(response_text)
            
            # Convert to Ingredient objects
            ingredients = []
            for item in ingredients_data:
                ingredients.append(Ingredient(
                    name=item.get('name', ''),
                    confidence=float(item.get('confidence', 0.5)),
                    quantity=item.get('quantity'),
                    unit=item.get('unit')
                ))
            
            return ingredients
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse ingredients response, using fallback: {str(e)}")
            # Fallback: try to extract ingredient names from text
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> List[Ingredient]:
        """
        Fallback parsing when JSON parsing fails
        
        Args:
            response_text: Raw response text
        
        Returns:
            List of Ingredient objects with basic parsing
        """
        # Simple fallback: extract potential ingredient names
        # This is a basic implementation - can be improved
        ingredients = []
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                # Basic heuristic: if line looks like an ingredient name
                if not line.startswith('{') and not line.startswith('['):
                    ingredients.append(Ingredient(
                        name=line.split(',')[0].strip(),
                        confidence=0.7,  # Default confidence
                        quantity=None,
                        unit=None
                    ))
        
        return ingredients[:10]  # Limit to 10 ingredients
