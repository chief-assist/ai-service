"""
API route definitions
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    IngredientRecognitionRequest,
    IngredientRecognitionResponse,
    RecipeSuggestionRequest,
    RecipeSuggestionResponse,
    RecipeDetailsRequest,
    RecipeDetailsResponse,
    PersonalizedSuggestionRequest,
    PersonalizedSuggestionResponse,
)
from app.middleware.auth import verify_api_key
from app.services.recognition_service import RecognitionService
from app.services.recipe_service import RecipeService

router = APIRouter()

# Initialize services
recognition_service = RecognitionService()
recipe_service = RecipeService()


@router.get(
    "",
    summary="Get API Information",
    description="Returns information about the API service and available endpoints",
    response_description="API information including service details and endpoint list",
    tags=["AI"]
)
async def api_info():
    """
    Get API information and available endpoints.
    
    This endpoint provides an overview of the ChefAssist AI Service, including:
    - Service name and version
    - List of all available endpoints with their methods and descriptions
    - Links to interactive documentation
    """
    return {
        "service": "ChefAssist AI Service",
        "version": "1.0.0",
        "endpoints": {
            "recognize_ingredients": {
                "method": "POST",
                "path": "/api/ai/recognize-ingredients",
                "description": "Recognize ingredients from uploaded images"
            },
            "suggest_recipes": {
                "method": "POST",
                "path": "/api/ai/suggest-recipes",
                "description": "Get recipe suggestions based on ingredients"
            },
            "generate_recipe_details": {
                "method": "POST",
                "path": "/api/ai/generate-recipe-details",
                "description": "Generate detailed recipe instructions"
            },
            "personalize_suggestions": {
                "method": "POST",
                "path": "/api/ai/personalize-suggestions",
                "description": "Get personalized recipe suggestions"
            },
            "health": {
                "method": "GET",
                "path": "/api/ai/health",
                "description": "Service health check"
            }
        },
        "documentation": "/docs",
        "redoc": "/redoc"
    }


@router.post(
    "/recognize-ingredients",
    response_model=IngredientRecognitionResponse,
    status_code=200,
    summary="Recognize Ingredients from Image",
    description="""
    Recognize ingredients from uploaded images using Google Gemini Vision AI.
    
    **Features:**
    - Supports both image URLs and base64-encoded images
    - Identifies multiple ingredients in a single image
    - Provides confidence scores for each ingredient
    - Detects quantities and units when possible
    
    **Image Requirements:**
    - Supported formats: JPEG, PNG, WebP
    - Maximum size: 10MB
    - Recommended: Clear, well-lit images of ingredients
    """,
    response_description="List of recognized ingredients with confidence scores and metadata",
    tags=["AI"],
    responses={
        200: {
            "description": "Successful ingredient recognition",
            "content": {
                "application/json": {
                    "example": {
                        "ingredients": [
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
                        ],
                        "processing_time": 1.2
                    }
                }
            }
        },
        400: {"description": "Invalid request - missing image or invalid format"},
        401: {"description": "Unauthorized - missing or invalid API key"},
        500: {"description": "Internal server error - AI service unavailable"}
    }
)
async def recognize_ingredients(
    request: IngredientRecognitionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Recognize ingredients from uploaded images using Gemini AI.
    
    This endpoint uses Google Gemini Vision AI to analyze images and identify
    food ingredients. It supports both image URLs and base64-encoded images.
    """
    try:
        result = await recognition_service.recognize_ingredients(request)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        # Fallback for unexpected errors
        logger.error(f"Unexpected error in recognize_ingredients endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")


@router.post(
    "/suggest-recipes",
    response_model=RecipeSuggestionResponse,
    status_code=200,
    summary="Get Recipe Suggestions",
    description="""
    Generate recipe suggestions based on available ingredients.
    
    **Features:**
    - Sorts recipes by ingredient completeness (highest match first)
    - Supports filtering by dietary restrictions, cuisine, cooking time, and difficulty
    - Returns recipes with missing ingredients identified
    - Provides match percentage for each recipe
    
    **Filtering Options:**
    - Dietary restrictions: vegetarian, vegan, gluten-free, dairy-free, keto, paleo, etc.
    - Cuisine type: Italian, Asian, Mexican, Mediterranean, American, etc.
    - Cooking time: Maximum time in minutes
    - Difficulty: beginner, intermediate, advanced
    - Meal type: breakfast, lunch, dinner, snack, dessert
    """,
    response_description="List of suggested recipes sorted by ingredient match percentage",
    tags=["AI"],
    responses={
        200: {
            "description": "Successful recipe suggestions",
            "content": {
                "application/json": {
                    "example": {
                        "recipes": [
                            {
                                "id": "recipe_123",
                                "name": "Tomato Pasta",
                                "description": "Simple and delicious pasta dish",
                                "ingredients_required": ["tomato", "onion", "garlic", "pasta"],
                                "ingredients_missing": [],
                                "match_percentage": 100.0,
                                "cooking_time": 25,
                                "difficulty": "beginner",
                                "cuisine": "italian",
                                "dietary_info": ["vegetarian"]
                            }
                        ],
                        "total_results": 1
                    }
                }
            }
        },
        400: {"description": "Invalid request - missing ingredients or invalid filters"},
        401: {"description": "Unauthorized - missing or invalid API key"},
        500: {"description": "Internal server error - recipe generation failed"}
    }
)
async def suggest_recipes(
    request: RecipeSuggestionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate recipe suggestions based on available ingredients.
    
    Recipes are automatically sorted by ingredient completeness, with the most
    complete matches appearing first. You can filter results by dietary preferences,
    cuisine type, cooking time, and difficulty level.
    """
    try:
        result = await recipe_service.suggest_recipes(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe suggestion failed: {str(e)}")


@router.post(
    "/generate-recipe-details",
    response_model=RecipeDetailsResponse,
    status_code=200,
    summary="Generate Recipe Details",
    description="""
    Generate detailed recipe instructions and cooking steps.
    
    **Features:**
    - Step-by-step cooking instructions with durations
    - Complete ingredient list with quantities and units
    - Nutritional information (calories, protein, carbs, fat)
    - Prep time, cooking time, and total time
    - Difficulty level and serving information
    
    **Use Cases:**
    - Generate full recipe from recipe name and available ingredients
    - Create detailed cooking instructions for suggested recipes
    - Get nutritional information for meal planning
    """,
    response_description="Complete recipe details with instructions, ingredients, and metadata",
    tags=["AI"],
    responses={
        200: {
            "description": "Successful recipe generation",
            "content": {
                "application/json": {
                    "example": {
                        "recipe_id": "recipe_123",
                        "name": "Tomato Pasta",
                        "description": "A classic Italian pasta dish",
                        "ingredients": [
                            {"name": "pasta", "quantity": "400", "unit": "g"},
                            {"name": "tomato", "quantity": "3", "unit": "pieces"}
                        ],
                        "instructions": [
                            {"step": 1, "description": "Boil water in a large pot", "duration": 10},
                            {"step": 2, "description": "Add pasta and cook until al dente", "duration": 12}
                        ],
                        "cooking_time": 25,
                        "prep_time": 10,
                        "total_time": 35,
                        "servings": 4,
                        "difficulty": "beginner",
                        "nutrition": {
                            "calories": 350,
                            "protein": 12,
                            "carbs": 65,
                            "fat": 8
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request - missing recipe name or ingredients"},
        401: {"description": "Unauthorized - missing or invalid API key"},
        500: {"description": "Internal server error - recipe generation failed"}
    }
)
async def generate_recipe_details(
    request: RecipeDetailsRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate detailed recipe instructions and steps.
    
    Creates a complete recipe with step-by-step instructions, ingredient quantities,
    cooking times, and nutritional information using AI-powered recipe generation.
    """
    try:
        result = await recipe_service.generate_recipe_details(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")


@router.post(
    "/personalize-suggestions",
    response_model=PersonalizedSuggestionResponse,
    status_code=200,
    summary="Get Personalized Recipe Suggestions",
    description="""
    Generate personalized recipe suggestions based on user history and preferences.
    
    **Personalization Features:**
    - Analyzes cooking history to identify preferred recipes
    - Considers user ratings to understand taste preferences
    - Adapts to dietary restrictions and cuisine preferences
    - Provides explanation for recommendations
    
    **How It Works:**
    - Reviews past recipes and ratings to identify patterns
    - Matches current ingredients with user's preferred cuisine types
    - Prioritizes recipes similar to highly-rated dishes
    - Considers dietary restrictions and spice level preferences
    
    **Use Cases:**
    - Personalized meal planning
    - Discover new recipes based on cooking history
    - Get recommendations aligned with dietary preferences
    """,
    response_description="Personalized recipe suggestions with recommendation reasoning",
    tags=["AI"],
    responses={
        200: {
            "description": "Successful personalized suggestions",
            "content": {
                "application/json": {
                    "example": {
                        "recipes": [
                            {
                                "id": "recipe_456",
                                "name": "Mediterranean Pasta",
                                "description": "Inspired by your love for Italian cuisine",
                                "ingredients_required": ["tomato", "onion", "pasta"],
                                "ingredients_missing": [],
                                "match_percentage": 100.0,
                                "cooking_time": 30,
                                "difficulty": "beginner",
                                "cuisine": "italian",
                                "dietary_info": ["vegetarian"]
                            }
                        ],
                        "personalization_score": 0.92,
                        "recommendation_reason": "Based on your preference for Italian cuisine, similar to recipes you've highly rated"
                    }
                }
            }
        },
        400: {"description": "Invalid request - missing user_id or ingredients"},
        401: {"description": "Unauthorized - missing or invalid API key"},
        500: {"description": "Internal server error - personalization failed"}
    }
)
async def personalize_suggestions(
    request: PersonalizedSuggestionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate personalized recipe suggestions based on user history and preferences.
    
    This endpoint uses machine learning to analyze user cooking history, ratings,
    and preferences to provide tailored recipe recommendations that match their
    culinary style and dietary needs.
    """
    try:
        result = await recipe_service.personalize_suggestions(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")
