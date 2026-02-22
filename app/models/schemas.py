"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


# Ingredient Recognition Models
class Ingredient(BaseModel):
    """Recognized ingredient model"""
    name: str = Field(..., description="Ingredient name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recognition confidence score")
    quantity: Optional[str] = Field(None, description="Detected quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class IngredientRecognitionRequest(BaseModel):
    """Request model for ingredient recognition"""
    image_url: Optional[HttpUrl] = Field(None, description="URL of the image to recognize")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://cloudinary.com/image.jpg"
            }
        }


class IngredientRecognitionResponse(BaseModel):
    """Response model for ingredient recognition"""
    ingredients: List[Ingredient] = Field(..., description="List of recognized ingredients")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": [
                    {
                        "name": "tomato",
                        "confidence": 0.95,
                        "quantity": "3",
                        "unit": "pieces"
                    }
                ],
                "processing_time": 1.2
            }
        }


# Recipe Suggestion Models
class RecipeFilters(BaseModel):
    """Recipe filtering options"""
    dietary_restrictions: Optional[List[str]] = Field(default=[], description="Dietary restrictions")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    cooking_time: Optional[int] = Field(None, ge=0, description="Maximum cooking time in minutes")
    difficulty: Optional[str] = Field(None, description="Difficulty level: beginner, intermediate, advanced")
    meal_type: Optional[str] = Field(None, description="Meal type: breakfast, lunch, dinner, snack, dessert")
    exclude_ingredients: Optional[List[str]] = Field(default=[], description="Ingredients to exclude")


class Recipe(BaseModel):
    """Recipe model"""
    id: str = Field(..., description="Recipe identifier")
    name: str = Field(..., description="Recipe name")
    description: str = Field(..., description="Recipe description")
    ingredients_required: List[str] = Field(..., description="Required ingredients")
    ingredients_missing: List[str] = Field(default=[], description="Missing ingredients")
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Ingredient match percentage")
    cooking_time: int = Field(..., ge=0, description="Cooking time in minutes")
    difficulty: str = Field(..., description="Difficulty level")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    dietary_info: List[str] = Field(default=[], description="Dietary information")
    image_url: Optional[str] = Field(None, description="Recipe image URL")


class RecipeSuggestionRequest(BaseModel):
    """Request model for recipe suggestions"""
    ingredients: List[str] = Field(..., min_items=1, description="List of available ingredients")
    filters: Optional[RecipeFilters] = Field(None, description="Recipe filters")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": ["tomato", "onion", "garlic", "pasta"],
                "filters": {
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine": "italian",
                    "cooking_time": 30,
                    "difficulty": "beginner"
                },
                "max_results": 10
            }
        }


class RecipeSuggestionResponse(BaseModel):
    """Response model for recipe suggestions"""
    recipes: List[Recipe] = Field(..., description="List of suggested recipes")
    total_results: int = Field(..., description="Total number of results")


# Recipe Details Models
class RecipeIngredient(BaseModel):
    """Recipe ingredient with quantity"""
    name: str = Field(..., description="Ingredient name")
    quantity: str = Field(..., description="Quantity")
    unit: str = Field(..., description="Unit of measurement")


class RecipeInstruction(BaseModel):
    """Recipe instruction step"""
    step: int = Field(..., ge=1, description="Step number")
    description: str = Field(..., description="Step description")
    duration: Optional[int] = Field(None, ge=0, description="Step duration in minutes")


class NutritionInfo(BaseModel):
    """Nutritional information"""
    calories: Optional[int] = Field(None, ge=0, description="Calories per serving")
    protein: Optional[float] = Field(None, ge=0, description="Protein in grams")
    carbs: Optional[float] = Field(None, ge=0, description="Carbohydrates in grams")
    fat: Optional[float] = Field(None, ge=0, description="Fat in grams")


class RecipeDetailsRequest(BaseModel):
    """Request model for recipe details generation"""
    recipe_name: str = Field(..., min_length=1, description="Recipe name")
    ingredients: List[str] = Field(..., min_items=1, description="Available ingredients")
    servings: int = Field(default=4, ge=1, description="Number of servings")
    cooking_time: Optional[int] = Field(None, ge=0, description="Desired cooking time in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recipe_name": "Tomato Pasta",
                "ingredients": ["tomato", "onion", "garlic", "pasta"],
                "servings": 4,
                "cooking_time": 25
            }
        }


class RecipeDetailsResponse(BaseModel):
    """Response model for recipe details"""
    recipe_id: str = Field(..., description="Recipe identifier")
    name: str = Field(..., description="Recipe name")
    description: str = Field(..., description="Recipe description")
    ingredients: List[RecipeIngredient] = Field(..., description="Recipe ingredients")
    instructions: List[RecipeInstruction] = Field(..., description="Cooking instructions")
    cooking_time: int = Field(..., ge=0, description="Cooking time in minutes")
    prep_time: int = Field(..., ge=0, description="Preparation time in minutes")
    total_time: int = Field(..., ge=0, description="Total time in minutes")
    servings: int = Field(..., ge=1, description="Number of servings")
    difficulty: str = Field(..., description="Difficulty level")
    nutrition: Optional[NutritionInfo] = Field(None, description="Nutritional information")


# Personalized Suggestions Models
class CookingHistoryEntry(BaseModel):
    """User cooking history entry"""
    recipe_id: str = Field(..., description="Recipe identifier")
    rating: int = Field(..., ge=1, le=5, description="User rating")
    cooked_at: str = Field(..., description="Date when recipe was cooked")


class UserPreferences(BaseModel):
    """User preferences"""
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    cuisine_preferences: List[str] = Field(default=[], description="Preferred cuisines")
    spice_level: Optional[str] = Field(None, description="Preferred spice level")


class PersonalizedSuggestionRequest(BaseModel):
    """Request model for personalized suggestions"""
    ingredients: List[str] = Field(..., min_items=1, description="Available ingredients")
    user_id: str = Field(..., description="User identifier")
    cooking_history: List[CookingHistoryEntry] = Field(default=[], description="User cooking history")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": ["tomato", "onion"],
                "user_id": "user_123",
                "cooking_history": [
                    {
                        "recipe_id": "recipe_456",
                        "rating": 5,
                        "cooked_at": "2024-01-15"
                    }
                ],
                "preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_preferences": ["italian", "mediterranean"],
                    "spice_level": "medium"
                }
            }
        }


class PersonalizedSuggestionResponse(BaseModel):
    """Response model for personalized suggestions"""
    recipes: List[Recipe] = Field(..., description="Personalized recipe suggestions")
    personalization_score: float = Field(..., ge=0.0, le=1.0, description="Personalization score")
    recommendation_reason: Optional[str] = Field(None, description="Reason for recommendations")


# Error Models
class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: ErrorDetail = Field(..., description="Error information")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
