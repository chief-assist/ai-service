"""
Models package - Pydantic schemas and request/response models
"""
from app.models.schemas import (
    # Ingredient Recognition
    Ingredient,
    IngredientRecognitionRequest,
    IngredientRecognitionResponse,
    # Recipe Suggestions
    RecipeFilters,
    Recipe,
    RecipeSuggestionRequest,
    RecipeSuggestionResponse,
    # Recipe Details
    RecipeIngredient,
    RecipeInstruction,
    NutritionInfo,
    RecipeDetailsRequest,
    RecipeDetailsResponse,
    # Personalized Suggestions
    CookingHistoryEntry,
    UserPreferences,
    PersonalizedSuggestionRequest,
    PersonalizedSuggestionResponse,
    # Error Models
    ErrorDetail,
    ErrorResponse,
)

__all__ = [
    "Ingredient",
    "IngredientRecognitionRequest",
    "IngredientRecognitionResponse",
    "RecipeFilters",
    "Recipe",
    "RecipeSuggestionRequest",
    "RecipeSuggestionResponse",
    "RecipeIngredient",
    "RecipeInstruction",
    "NutritionInfo",
    "RecipeDetailsRequest",
    "RecipeDetailsResponse",
    "CookingHistoryEntry",
    "UserPreferences",
    "PersonalizedSuggestionRequest",
    "PersonalizedSuggestionResponse",
    "ErrorDetail",
    "ErrorResponse",
]
