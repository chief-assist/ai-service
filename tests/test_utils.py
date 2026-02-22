"""
Tests for utility functions
"""
import pytest
from app.utils.validators import validate_image_url, validate_base64_image, validate_ingredient_list
from app.utils.text_utils import extract_json_from_text, clean_text


def test_validate_image_url():
    """Test image URL validation"""
    assert validate_image_url("https://example.com/image.jpg") == True
    assert validate_image_url("http://example.com/image.jpg") == True
    assert validate_image_url("invalid-url") == False


def test_validate_ingredient_list():
    """Test ingredient list validation"""
    assert validate_ingredient_list(["tomato", "onion"]) == True
    assert validate_ingredient_list([]) == False
    assert validate_ingredient_list("not a list") == False


def test_clean_text():
    """Test text cleaning"""
    text = "  Hello   World  "
    assert clean_text(text) == "Hello World"
