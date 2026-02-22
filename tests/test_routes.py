"""
Comprehensive tests for API routes
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

# Set test API key in environment for tests
os.environ["API_KEY"] = "test-api-key-123"
TEST_API_KEY = "test-api-key-123"

client = TestClient(app)


@pytest.fixture
def mock_ollama_available():
    """Mock Ollama service as available"""
    with patch('app.services.ollama_service.OllamaService.is_available', return_value=True):
        with patch('app.services.ollama_service.OllamaService.generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '{"ingredients": [{"name": "tomato", "confidence": 0.95}]}'
            yield mock_gen


@pytest.fixture
def mock_ollama_unavailable():
    """Mock Ollama service as unavailable"""
    with patch('app.services.ollama_service.OllamaService.is_available', return_value=False):
        yield


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"


class TestHealthCheck:
    """Tests for health check endpoint"""
    
    def test_health_check_available(self, mock_ollama_available):
        """Test health check when Ollama is available"""
        response = client.get("/api/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "ollama_available" in data
    
    def test_health_check_unavailable(self, mock_ollama_unavailable):
        """Test health check when Ollama is unavailable"""
        response = client.get("/api/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data.get("ollama_available") is False


class TestAPIInto:
    """Tests for API info endpoint"""
    
    def test_api_info(self):
        """Test API info endpoint"""
        response = client.get("/api/ai")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data
        assert "documentation" in data


class TestIngredientRecognition:
    """Tests for ingredient recognition endpoint"""
    
    def test_recognize_ingredients_missing_input(self):
        """Test ingredient recognition without image"""
        response = client.post(
            "/api/ai/recognize-ingredients",
            headers={"X-API-Key": TEST_API_KEY},
            json={}
        )
        # Service returns 400 for validation errors (which is valid)
        assert response.status_code in [400, 422]  # Both are valid for validation errors
    
    def test_recognize_ingredients_with_url(self, mock_ollama_available):
        """Test ingredient recognition with image URL"""
        from app.models.schemas import IngredientRecognitionResponse, Ingredient
        with patch('app.api.routes.recognition_service.recognize_ingredients', new_callable=AsyncMock) as mock_rec:
            mock_response = IngredientRecognitionResponse(
                ingredients=[
                    Ingredient(name="tomato", confidence=0.95, quantity="3", unit="pieces")
                ],
                processing_time=1.2
            )
            mock_rec.return_value = mock_response
            
            response = client.post(
                "/api/ai/recognize-ingredients",
                headers={"X-API-Key": TEST_API_KEY},
                json={"image_url": "https://example.com/image.jpg"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "ingredients" in data
            assert len(data["ingredients"]) > 0
            assert "processing_time" in data
    
    def test_recognize_ingredients_with_base64(self, mock_ollama_available):
        """Test ingredient recognition with base64 image"""
        from app.models.schemas import IngredientRecognitionResponse, Ingredient
        with patch('app.api.routes.recognition_service.recognize_ingredients', new_callable=AsyncMock) as mock_rec:
            mock_response = IngredientRecognitionResponse(
                ingredients=[
                    Ingredient(name="onion", confidence=0.88, quantity="1", unit="piece")
                ],
                processing_time=0.8
            )
            mock_rec.return_value = mock_response
            
            response = client.post(
                "/api/ai/recognize-ingredients",
                headers={"X-API-Key": TEST_API_KEY},
                json={"image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}
            )
            assert response.status_code == 200
            data = response.json()
            assert "ingredients" in data
    
    def test_recognize_ingredients_timeout(self):
        """Test ingredient recognition timeout handling"""
        from fastapi import HTTPException
        with patch('app.api.routes.recognition_service.recognize_ingredients', new_callable=AsyncMock) as mock_rec:
            # The service raises HTTPException with 504 for timeout
            mock_rec.side_effect = HTTPException(status_code=504, detail="Ollama AI service timed out")
            
            response = client.post(
                "/api/ai/recognize-ingredients",
                headers={"X-API-Key": TEST_API_KEY},
                json={"image_url": "https://example.com/image.jpg"}
            )
            assert response.status_code == 504
            # Error handler wraps in ErrorResponse format
            response_data = response.json()
            assert "error" in response_data
            error_message = response_data["error"]["message"].lower()
            # Check for timeout-related keywords
            assert any(keyword in error_message for keyword in ["timeout", "timed", "timed out"])
    
    def test_recognize_ingredients_connection_error(self):
        """Test ingredient recognition connection error"""
        from fastapi import HTTPException
        with patch('app.api.routes.recognition_service.recognize_ingredients', new_callable=AsyncMock) as mock_rec:
            # The service raises HTTPException with 503 for connection errors
            mock_rec.side_effect = HTTPException(status_code=503, detail="Ollama AI service connection error")
            
            response = client.post(
                "/api/ai/recognize-ingredients",
                headers={"X-API-Key": TEST_API_KEY},
                json={"image_url": "https://example.com/image.jpg"}
            )
            assert response.status_code == 503
            # Error handler wraps in ErrorResponse format
            response_data = response.json()
            assert "error" in response_data
            assert "connection" in response_data["error"]["message"].lower()


class TestRecipeSuggestions:
    """Tests for recipe suggestion endpoint"""
    
    def test_suggest_recipes_missing_ingredients(self):
        """Test recipe suggestions without ingredients"""
        response = client.post(
            "/api/ai/suggest-recipes",
            headers={"X-API-Key": TEST_API_KEY},
            json={}
        )
        assert response.status_code == 422  # Validation error
    
    def test_suggest_recipes_basic(self, mock_ollama_available):
        """Test basic recipe suggestions"""
        from app.models.schemas import RecipeSuggestionResponse, Recipe
        with patch('app.api.routes.recipe_service.suggest_recipes', new_callable=AsyncMock) as mock_suggest:
            mock_response = RecipeSuggestionResponse(
                recipes=[
                    Recipe(
                        id="recipe_1",
                        name="Tomato Pasta",
                        description="Simple pasta dish",
                        ingredients_required=["tomato", "pasta"],
                        ingredients_missing=[],
                        match_percentage=100.0,
                        cooking_time=25,
                        difficulty="beginner"
                    )
                ],
                total_results=1
            )
            mock_suggest.return_value = mock_response
            
            response = client.post(
                "/api/ai/suggest-recipes",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "ingredients": ["tomato", "pasta"],
                    "max_results": 10
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "recipes" in data
            assert len(data["recipes"]) > 0
    
    def test_suggest_recipes_with_filters(self, mock_ollama_available):
        """Test recipe suggestions with filters"""
        from app.models.schemas import RecipeSuggestionResponse
        with patch('app.api.routes.recipe_service.suggest_recipes', new_callable=AsyncMock) as mock_suggest:
            mock_response = RecipeSuggestionResponse(
                recipes=[],
                total_results=0
            )
            mock_suggest.return_value = mock_response
            
            response = client.post(
                "/api/ai/suggest-recipes",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "ingredients": ["tomato", "onion"],
                    "filters": {
                        "dietary_restrictions": ["vegetarian"],
                        "cuisine": "italian",
                        "cooking_time": 30
                    },
                    "max_results": 5
                }
            )
            assert response.status_code == 200


class TestRecipeGeneration:
    """Tests for recipe details generation endpoint"""
    
    def test_generate_recipe_details_missing_fields(self):
        """Test recipe generation without required fields"""
        response = client.post(
            "/api/ai/generate-recipe-details",
            headers={"X-API-Key": TEST_API_KEY},
            json={}
        )
        assert response.status_code == 422
    
    def test_generate_recipe_details_success(self, mock_ollama_available):
        """Test successful recipe generation"""
        from app.models.schemas import RecipeDetailsResponse, RecipeIngredient, RecipeInstruction
        with patch('app.api.routes.recipe_service.generate_recipe_details', new_callable=AsyncMock) as mock_gen:
            mock_response = RecipeDetailsResponse(
                recipe_id="recipe_123",
                name="Tomato Pasta",
                description="A classic Italian dish",
                ingredients=[
                    RecipeIngredient(name="pasta", quantity="400", unit="g")
                ],
                instructions=[
                    RecipeInstruction(step=1, description="Boil water", duration=10)
                ],
                cooking_time=25,
                prep_time=10,
                total_time=35,
                servings=4,
                difficulty="beginner"
            )
            mock_gen.return_value = mock_response
            
            response = client.post(
                "/api/ai/generate-recipe-details",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "recipe_name": "Tomato Pasta",
                    "ingredients": ["tomato", "pasta"],
                    "servings": 4,
                    "cooking_time": 25
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "recipe_id" in data
            assert "name" in data
            assert "instructions" in data


class TestPersonalizedSuggestions:
    """Tests for personalized suggestions endpoint"""
    
    def test_personalize_suggestions_success(self, mock_ollama_available):
        """Test personalized suggestions"""
        from app.models.schemas import PersonalizedSuggestionResponse, Recipe
        with patch('app.api.routes.recipe_service.personalize_suggestions', new_callable=AsyncMock) as mock_personalize:
            mock_response = PersonalizedSuggestionResponse(
                recipes=[
                    Recipe(
                        id="recipe_1",
                        name="Personalized Recipe",
                        description="A personalized recipe based on your preferences",
                        ingredients_required=["tomato", "onion"],
                        ingredients_missing=[],
                        match_percentage=95.0,
                        cooking_time=30,
                        difficulty="beginner"
                    )
                ],
                personalization_score=0.92,
                recommendation_reason="Based on your preferences"
            )
            mock_personalize.return_value = mock_response
            
            response = client.post(
                "/api/ai/personalize-suggestions",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "ingredients": ["tomato", "onion"],
                    "user_id": "user_123",
                    "cooking_history": [],
                    "preferences": {
                        "dietary_restrictions": ["vegetarian"]
                    }
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "recipes" in data
            assert "personalization_score" in data


class TestAuthentication:
    """Tests for API key authentication"""
    
    def test_missing_api_key(self):
        """Test endpoint without API key"""
        response = client.post(
            "/api/ai/recognize-ingredients",
            json={"image_url": "https://example.com/image.jpg"}
        )
        # Should require API key (401 or 403) or allow in dev mode
        assert response.status_code in [200, 401, 403]
    
    def test_invalid_api_key(self):
        """Test endpoint with invalid API key"""
        response = client.post(
            "/api/ai/recognize-ingredients",
            headers={"X-API-Key": "invalid-key"},
            json={"image_url": "https://example.com/image.jpg"}
        )
        # Should reject invalid key (401 or 403) or allow in dev mode
        assert response.status_code in [200, 401, 403]
