"""
Recipe generation and suggestion service
"""
import logging
from typing import List, Dict, Any
from app.models.schemas import (
    RecipeSuggestionRequest,
    RecipeSuggestionResponse,
    Recipe,
    RecipeDetailsRequest,
    RecipeDetailsResponse,
    RecipeIngredient,
    RecipeInstruction,
    NutritionInfo,
    PersonalizedSuggestionRequest,
    PersonalizedSuggestionResponse,
    CookingHistoryEntry,
)
from app.services.gemini_service import GeminiService
import json
import re

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe generation and suggestions"""
    
    def __init__(self):
        """Initialize recipe service"""
        self.gemini_service = GeminiService()
    
    async def suggest_recipes(
        self,
        request: RecipeSuggestionRequest
    ) -> RecipeSuggestionResponse:
        """
        Generate recipe suggestions based on ingredients
        
        Args:
            request: Recipe suggestion request
        
        Returns:
            Recipe suggestions response
        """
        try:
            # Build prompt for recipe suggestions
            prompt = self._build_suggestion_prompt(request)
            
            # Generate recipes using Gemini
            response_text = await self.gemini_service.generate_text(prompt)
            
            # Parse response into recipes
            recipes = self._parse_recipes_response(response_text, request.ingredients)
            
            # Apply filters if provided
            if request.filters:
                recipes = self._apply_filters(recipes, request.filters)
            
            # Sort by match percentage (ingredient completeness)
            recipes.sort(key=lambda r: r.match_percentage, reverse=True)
            
            # Limit results
            recipes = recipes[:request.max_results]
            
            return RecipeSuggestionResponse(
                recipes=recipes,
                total_results=len(recipes)
            )
            
        except Exception as e:
            logger.error(f"Recipe suggestion failed: {str(e)}")
            raise
    
    async def generate_recipe_details(
        self,
        request: RecipeDetailsRequest
    ) -> RecipeDetailsResponse:
        """
        Generate detailed recipe instructions
        
        Args:
            request: Recipe details request
        
        Returns:
            Recipe details response
        """
        try:
            # Build prompt for recipe generation
            prompt = self._build_recipe_generation_prompt(request)
            
            # Generate recipe using Gemini
            response_text = await self.gemini_service.generate_text(prompt)
            
            # Parse response into recipe details
            recipe_details = self._parse_recipe_details_response(response_text, request)
            
            return recipe_details
            
        except Exception as e:
            logger.error(f"Recipe generation failed: {str(e)}")
            raise
    
    async def personalize_suggestions(
        self,
        request: PersonalizedSuggestionRequest
    ) -> PersonalizedSuggestionResponse:
        """
        Generate personalized recipe suggestions
        
        Args:
            request: Personalized suggestion request
        
        Returns:
            Personalized suggestions response
        """
        try:
            # Build personalized prompt
            prompt = self._build_personalized_prompt(request)
            
            # Generate recipes using Gemini
            response_text = await self.gemini_service.generate_text(prompt)
            
            # Parse response
            recipes = self._parse_recipes_response(response_text, request.ingredients)
            
            # Calculate personalization score based on history and preferences
            personalization_score = self._calculate_personalization_score(
                recipes,
                request.cooking_history,
                request.preferences
            )
            
            # Sort by personalization
            recipes.sort(key=lambda r: r.match_percentage, reverse=True)
            recipes = recipes[:request.max_results]
            
            # Generate recommendation reason
            recommendation_reason = self._generate_recommendation_reason(
                recipes,
                request.cooking_history,
                request.preferences
            )
            
            return PersonalizedSuggestionResponse(
                recipes=recipes,
                personalization_score=personalization_score,
                recommendation_reason=recommendation_reason
            )
            
        except Exception as e:
            logger.error(f"Personalization failed: {str(e)}")
            raise
    
    def _build_suggestion_prompt(self, request: RecipeSuggestionRequest) -> str:
        """Build prompt for recipe suggestions"""
        ingredients_str = ', '.join(request.ingredients)
        
        prompt = f"""Generate {request.max_results} recipe suggestions using these ingredients: {ingredients_str}

For each recipe, provide:
- name: Recipe name
- description: Brief description
- ingredients_required: List of all required ingredients
- ingredients_missing: Ingredients not in the provided list
- match_percentage: Percentage of required ingredients that are available (0-100)
- cooking_time: Cooking time in minutes
- difficulty: beginner, intermediate, or advanced
- cuisine: Cuisine type
- dietary_info: List of dietary tags (vegetarian, vegan, gluten-free, etc.)

"""
        
        if request.filters:
            if request.filters.dietary_restrictions:
                prompt += f"Dietary restrictions: {', '.join(request.filters.dietary_restrictions)}\n"
            if request.filters.cuisine:
                prompt += f"Cuisine preference: {request.filters.cuisine}\n"
            if request.filters.cooking_time:
                prompt += f"Maximum cooking time: {request.filters.cooking_time} minutes\n"
            if request.filters.difficulty:
                prompt += f"Difficulty level: {request.filters.difficulty}\n"
        
        prompt += """
Return the response as a JSON array of recipes:
[
    {
        "id": "recipe_1",
        "name": "Recipe Name",
        "description": "Recipe description",
        "ingredients_required": ["ingredient1", "ingredient2"],
        "ingredients_missing": [],
        "match_percentage": 100,
        "cooking_time": 30,
        "difficulty": "beginner",
        "cuisine": "italian",
        "dietary_info": ["vegetarian"]
    }
]
"""
        return prompt
    
    def _build_recipe_generation_prompt(self, request: RecipeDetailsRequest) -> str:
        """Build prompt for recipe generation"""
        ingredients_str = ', '.join(request.ingredients)
        
        prompt = f"""Generate a detailed recipe for: {request.recipe_name}

Available ingredients: {ingredients_str}
Servings: {request.servings}
"""
        
        if request.cooking_time:
            prompt += f"Target cooking time: {request.cooking_time} minutes\n"
        
        prompt += """
Provide a complete recipe with:
- description: Detailed recipe description
- ingredients: List with quantities and units
- instructions: Step-by-step cooking instructions with step numbers
- prep_time: Preparation time in minutes
- cooking_time: Cooking time in minutes
- total_time: Total time (prep + cooking)
- difficulty: beginner, intermediate, or advanced
- nutrition: Estimated nutritional information (calories, protein, carbs, fat)

Return as JSON:
{
    "description": "...",
    "ingredients": [
        {"name": "ingredient", "quantity": "amount", "unit": "unit"}
    ],
    "instructions": [
        {"step": 1, "description": "...", "duration": 5}
    ],
    "prep_time": 10,
    "cooking_time": 25,
    "total_time": 35,
    "difficulty": "beginner",
    "nutrition": {
        "calories": 350,
        "protein": 12,
        "carbs": 65,
        "fat": 8
    }
}
"""
        return prompt
    
    def _build_personalized_prompt(self, request: PersonalizedSuggestionRequest) -> str:
        """Build prompt for personalized suggestions"""
        ingredients_str = ', '.join(request.ingredients)
        
        prompt = f"""Generate personalized recipe suggestions using these ingredients: {ingredients_str}

User Context:
"""
        
        if request.cooking_history:
            prompt += "Cooking History:\n"
            for entry in request.cooking_history[:5]:  # Last 5 recipes
                prompt += f"- Recipe {entry.recipe_id}: Rating {entry.rating}/5\n"
        
        if request.preferences:
            if request.preferences.dietary_restrictions:
                prompt += f"Dietary restrictions: {', '.join(request.preferences.dietary_restrictions)}\n"
            if request.preferences.cuisine_preferences:
                prompt += f"Preferred cuisines: {', '.join(request.preferences.cuisine_preferences)}\n"
            if request.preferences.spice_level:
                prompt += f"Spice level preference: {request.preferences.spice_level}\n"
        
        prompt += """
Generate recipes that match the user's preferences and cooking history.
Prioritize recipes similar to highly-rated dishes in their history.

Return as JSON array of recipes (same format as regular suggestions).
"""
        return prompt
    
    def _parse_recipes_response(self, response_text: str, available_ingredients: List[str]) -> List[Recipe]:
        """Parse Gemini response into recipe list"""
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                recipes_data = json.loads(json_str)
            else:
                recipes_data = json.loads(response_text)
            
            recipes = []
            for idx, item in enumerate(recipes_data):
                # Calculate match percentage
                required = item.get('ingredients_required', [])
                missing = item.get('ingredients_missing', [])
                if required:
                    match_pct = ((len(required) - len(missing)) / len(required)) * 100
                else:
                    match_pct = 0.0
                
                recipes.append(Recipe(
                    id=item.get('id', f'recipe_{idx}'),
                    name=item.get('name', 'Unknown Recipe'),
                    description=item.get('description', ''),
                    ingredients_required=required,
                    ingredients_missing=missing,
                    match_percentage=match_pct,
                    cooking_time=item.get('cooking_time', 30),
                    difficulty=item.get('difficulty', 'beginner'),
                    cuisine=item.get('cuisine'),
                    dietary_info=item.get('dietary_info', []),
                    image_url=item.get('image_url')
                ))
            
            return recipes
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse recipes response: {str(e)}")
            raise ValueError("Invalid recipe response format")
    
    def _parse_recipe_details_response(
        self,
        response_text: str,
        request: RecipeDetailsRequest
    ) -> RecipeDetailsResponse:
        """Parse Gemini response into recipe details"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                recipe_data = json.loads(json_str)
            else:
                recipe_data = json.loads(response_text)
            
            # Parse ingredients
            ingredients = []
            for ing in recipe_data.get('ingredients', []):
                ingredients.append(RecipeIngredient(
                    name=ing.get('name', ''),
                    quantity=ing.get('quantity', ''),
                    unit=ing.get('unit', '')
                ))
            
            # Parse instructions
            instructions = []
            for inst in recipe_data.get('instructions', []):
                instructions.append(RecipeInstruction(
                    step=inst.get('step', len(instructions) + 1),
                    description=inst.get('description', ''),
                    duration=inst.get('duration')
                ))
            
            # Parse nutrition
            nutrition_data = recipe_data.get('nutrition', {})
            nutrition = None
            if nutrition_data:
                nutrition = NutritionInfo(
                    calories=nutrition_data.get('calories'),
                    protein=nutrition_data.get('protein'),
                    carbs=nutrition_data.get('carbs'),
                    fat=nutrition_data.get('fat')
                )
            
            return RecipeDetailsResponse(
                recipe_id=f"recipe_{hash(request.recipe_name)}",
                name=request.recipe_name,
                description=recipe_data.get('description', ''),
                ingredients=ingredients,
                instructions=instructions,
                cooking_time=recipe_data.get('cooking_time', request.cooking_time or 30),
                prep_time=recipe_data.get('prep_time', 10),
                total_time=recipe_data.get('total_time', recipe_data.get('prep_time', 10) + recipe_data.get('cooking_time', 30)),
                servings=request.servings,
                difficulty=recipe_data.get('difficulty', 'beginner'),
                nutrition=nutrition
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse recipe details: {str(e)}")
            raise ValueError("Invalid recipe details format")
    
    def _apply_filters(self, recipes: List[Recipe], filters) -> List[Recipe]:
        """Apply filters to recipe list"""
        filtered = recipes.copy()
        
        if filters.dietary_restrictions:
            filtered = [r for r in filtered if any(
                diet in r.dietary_info for diet in filters.dietary_restrictions
            )]
        
        if filters.cuisine:
            filtered = [r for r in filtered if r.cuisine == filters.cuisine]
        
        if filters.cooking_time:
            filtered = [r for r in filtered if r.cooking_time <= filters.cooking_time]
        
        if filters.difficulty:
            filtered = [r for r in filtered if r.difficulty == filters.difficulty]
        
        if filters.exclude_ingredients:
            filtered = [r for r in filtered if not any(
                ing in r.ingredients_required for ing in filters.exclude_ingredients
            )]
        
        return filtered
    
    def _calculate_personalization_score(
        self,
        recipes: List[Recipe],
        history: List[CookingHistoryEntry],
        preferences
    ) -> float:
        """Calculate personalization score"""
        if not history and not preferences:
            return 0.5  # Neutral score
        
        # Simple scoring based on history ratings
        if history:
            avg_rating = sum(h.rating for h in history) / len(history)
            return min(avg_rating / 5.0, 1.0)
        
        return 0.7  # Default score
    
    def _generate_recommendation_reason(
        self,
        recipes: List[Recipe],
        history: List[CookingHistoryEntry],
        preferences
    ) -> str:
        """Generate recommendation reason"""
        reasons = []
        
        if preferences and preferences.cuisine_preferences:
            reasons.append(f"Based on your preference for {', '.join(preferences.cuisine_preferences)} cuisine")
        
        if history:
            high_rated = [h for h in history if h.rating >= 4]
            if high_rated:
                reasons.append("similar to recipes you've highly rated")
        
        if not reasons:
            return "Based on your available ingredients and preferences"
        
        return ", ".join(reasons) + "."
