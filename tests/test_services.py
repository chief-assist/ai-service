"""
Tests for services
"""
import pytest
from app.services.gemini_service import GeminiService
from app.services.image_service import ImageService
from app.services.recognition_service import RecognitionService
from app.services.recipe_service import RecipeService


def test_gemini_service_initialization():
    """Test Gemini service initialization"""
    service = GeminiService()
    # Should initialize even without API key (will be unavailable)
    assert service is not None


def test_image_service():
    """Test image service"""
    service = ImageService()
    assert service is not None


def test_recognition_service_initialization():
    """Test recognition service initialization"""
    service = RecognitionService()
    assert service is not None


def test_recipe_service_initialization():
    """Test recipe service initialization"""
    service = RecipeService()
    assert service is not None
