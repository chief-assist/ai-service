"""
Comprehensive tests for services
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ollama_service import OllamaService
from app.services.image_service import ImageService
from app.services.recognition_service import RecognitionService
from app.services.recipe_service import RecipeService
from app.models.schemas import (
    IngredientRecognitionRequest,
    RecipeSuggestionRequest,
    RecipeDetailsRequest,
    PersonalizedSuggestionRequest
)


class TestOllamaService:
    """Tests for Ollama service"""
    
    @pytest.fixture
    def ollama_service(self):
        """Create Ollama service instance"""
        return OllamaService()
    
    def test_ollama_service_initialization(self, ollama_service):
        """Test Ollama service initialization"""
        assert ollama_service is not None
        assert ollama_service.ollama_url is not None
        assert ollama_service.model is not None
    
    def test_is_available(self, ollama_service):
        """Test availability check"""
        # Should return boolean
        result = ollama_service.is_available()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, ollama_service):
        """Test successful text generation"""
        with patch.object(ollama_service, '_check_connection', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            with patch.object(ollama_service.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "message": {
                        "content": "Generated text"
                    }
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                result = await ollama_service.generate_text("Test prompt")
                assert result == "Generated text"
    
    @pytest.mark.asyncio
    async def test_generate_text_timeout(self, ollama_service):
        """Test text generation timeout"""
        import asyncio
        with patch.object(ollama_service, '_check_connection', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            with patch.object(ollama_service.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = asyncio.TimeoutError("Request timed out")
                
                with pytest.raises(TimeoutError):
                    await ollama_service.generate_text("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_with_image(self, ollama_service):
        """Test image generation"""
        with patch.object(ollama_service, '_check_connection', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            with patch.object(ollama_service.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "message": {
                        "content": "Image analysis result"
                    }
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                image_data = b"fake_image_data"
                result = await ollama_service.generate_with_image("Analyze this image", image_data)
                assert result == "Image analysis result"
    
    @pytest.mark.asyncio
    async def test_generate_structured(self, ollama_service):
        """Test structured response generation"""
        with patch.object(ollama_service, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '{"name": "test", "value": 123}'
            
            result = await ollama_service.generate_structured(
                "Generate JSON",
                {"name": "string", "value": "number"}
            )
            assert isinstance(result, dict)
            assert "name" in result


class TestImageService:
    """Tests for image service"""
    
    @pytest.fixture
    def image_service(self):
        """Create image service instance"""
        return ImageService()
    
    def test_image_service_initialization(self, image_service):
        """Test image service initialization"""
        assert image_service is not None
    
    @pytest.mark.asyncio
    async def test_download_image_from_url(self, image_service):
        """Test downloading image from URL"""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = await image_service.download_image("https://example.com/image.jpg")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_download_image_invalid_url(self, image_service):
        """Test downloading image from invalid URL"""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            import httpx
            mock_get.side_effect = httpx.RequestError("Invalid URL")
            
            with pytest.raises(ValueError):
                await image_service.download_image("invalid-url")
    
    @pytest.mark.asyncio
    async def test_process_base64_image(self, image_service):
        """Test processing base64 encoded image"""
        import base64
        from io import BytesIO
        from PIL import Image
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        test_image.save(buffer, format='PNG')
        test_image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(test_image_bytes).decode('utf-8')
        
        # Decode base64 image
        decoded = base64.b64decode(base64_image)
        result = Image.open(BytesIO(decoded))
        assert result is not None
        assert result.size == (100, 100)


class TestRecognitionService:
    """Tests for recognition service"""
    
    @pytest.fixture
    def recognition_service(self):
        """Create recognition service instance"""
        return RecognitionService()
    
    def test_recognition_service_initialization(self, recognition_service):
        """Test recognition service initialization"""
        assert recognition_service is not None
    
    @pytest.mark.asyncio
    async def test_recognize_ingredients_success(self, recognition_service):
        """Test successful ingredient recognition"""
        with patch.object(recognition_service.ollama_service, 'generate_with_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '''
            [
                {
                    "name": "tomato",
                    "confidence": 0.95,
                    "quantity": "3",
                    "unit": "pieces"
                },
                {
                    "name": "onion",
                    "confidence": 0.88,
                    "quantity": "1",
                    "unit": "piece"
                }
            ]
            '''
            
            with patch.object(recognition_service.image_service, 'download_image', new_callable=AsyncMock) as mock_download:
                # Return bytes, not BytesIO - create valid image bytes
                from PIL import Image
                from io import BytesIO
                test_image = Image.new('RGB', (100, 100), color='red')
                buffer = BytesIO()
                test_image.save(buffer, format='JPEG')
                image_bytes = buffer.getvalue()
                mock_download.return_value = image_bytes
                
                # Mock validate_image - it doesn't return, just validates (raises on error)
                with patch.object(recognition_service.image_service, 'validate_image') as mock_validate:
                    # validate_image doesn't return, just validates
                    mock_validate.return_value = None
                    
                    with patch.object(recognition_service.image_service, 'process_image') as mock_process:
                        mock_image = Image.new('RGB', (100, 100))
                        mock_process.return_value = mock_image
                        
                        request = IngredientRecognitionRequest(image_url="https://example.com/image.jpg")
                        result = await recognition_service.recognize_ingredients(request)
                        
                        # Check Pydantic model attributes
                        assert hasattr(result, 'ingredients')
                        assert len(result.ingredients) > 0
                        assert hasattr(result, 'processing_time')
    
    @pytest.mark.asyncio
    async def test_recognize_ingredients_no_image(self, recognition_service):
        """Test recognition without image"""
        from fastapi import HTTPException
        request = IngredientRecognitionRequest()
        
        with pytest.raises(HTTPException) as exc_info:
            await recognition_service.recognize_ingredients(request)
        assert exc_info.value.status_code == 400


class TestRecipeService:
    """Tests for recipe service"""
    
    @pytest.fixture
    def recipe_service(self):
        """Create recipe service instance"""
        return RecipeService()
    
    def test_recipe_service_initialization(self, recipe_service):
        """Test recipe service initialization"""
        assert recipe_service is not None
    
    @pytest.mark.asyncio
    async def test_suggest_recipes_success(self, recipe_service):
        """Test successful recipe suggestions"""
        with patch.object(recipe_service.ollama_service, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '''
            {
                "recipes": [
                    {
                        "id": "recipe_1",
                        "name": "Tomato Pasta",
                        "description": "Simple pasta dish",
                        "ingredients_required": ["tomato", "pasta"],
                        "ingredients_missing": [],
                        "match_percentage": 100,
                        "cooking_time": 25,
                        "difficulty": "beginner"
                    }
                ]
            }
            '''
            
            request = RecipeSuggestionRequest(
                ingredients=["tomato", "pasta"],
                max_results=10
            )
            result = await recipe_service.suggest_recipes(request)
            
            # Check Pydantic model attributes, not dict keys
            assert hasattr(result, 'recipes')
            assert len(result.recipes) > 0
    
    @pytest.mark.asyncio
    async def test_generate_recipe_details_success(self, recipe_service):
        """Test successful recipe generation"""
        with patch.object(recipe_service.ollama_service, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '''
            {
                "recipe_id": "recipe_123",
                "name": "Tomato Pasta",
                "description": "A classic dish",
                "ingredients": [{"name": "pasta", "quantity": "400", "unit": "g"}],
                "instructions": [{"step": 1, "description": "Boil water", "duration": 10}],
                "cooking_time": 25,
                "prep_time": 10,
                "total_time": 35,
                "servings": 4,
                "difficulty": "beginner"
            }
            '''
            
            request = RecipeDetailsRequest(
                recipe_name="Tomato Pasta",
                ingredients=["tomato", "pasta"],
                servings=4,
                cooking_time=25
            )
            result = await recipe_service.generate_recipe_details(request)
            
            # Check Pydantic model attributes
            assert hasattr(result, 'recipe_id')
            assert hasattr(result, 'name')
            assert hasattr(result, 'instructions')
    
    @pytest.mark.asyncio
    async def test_personalize_suggestions_success(self, recipe_service):
        """Test successful personalized suggestions"""
        with patch.object(recipe_service.ollama_service, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '''
            {
                "recipes": [{"id": "recipe_1", "name": "Personalized Recipe"}],
                "personalization_score": 0.92,
                "recommendation_reason": "Based on your preferences"
            }
            '''
            
            request = PersonalizedSuggestionRequest(
                ingredients=["tomato", "onion"],
                user_id="user_123",
                cooking_history=[],
                preferences={"dietary_restrictions": ["vegetarian"]}
            )
            result = await recipe_service.personalize_suggestions(request)
            
            # Check Pydantic model attributes
            assert hasattr(result, 'recipes')
            assert hasattr(result, 'personalization_score')
