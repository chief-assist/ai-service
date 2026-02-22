"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.api.routes import router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title="ChefAssist AI Service",
    description="""
    ## AI/ML Microservice for ChefAssist
    
    This service provides AI-powered capabilities for the ChefAssist application:
    
    * **Ingredient Recognition**: Identify ingredients from images using Gemini Vision AI
    * **Recipe Suggestions**: Generate recipe recommendations based on available ingredients
    * **Recipe Generation**: Create detailed cooking instructions and steps
    * **Personalization**: Provide personalized recipe suggestions based on user history
    
    ### Authentication
    All endpoints require an API key in the `X-API-Key` header.
    
    ### Base URL
    `http://localhost:8000/api/ai`
    """,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "AI",
            "description": "AI-powered endpoints for ingredient recognition and recipe generation",
        },
        {
            "name": "Health",
            "description": "Service health and status endpoints",
        },
    ],
    contact={
        "name": "ChefAssist API Support",
        "email": "support@chefassist.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Add security scheme for API key
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Add security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key for authentication. Get your API key from the service administrator."
    }
    # Apply security to all endpoints (except health check and root)
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # Skip security for public endpoints
                if path not in ["/", "/api/ai/health"]:
                    if "security" not in operation:
                        operation["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (optional, can be enabled)
# app.add_middleware(RateLimitMiddleware)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(router, prefix="/api/ai", tags=["AI"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "status": "running"
    }


@app.get(
    "/api/ai/health",
    summary="Health Check",
    description="Check the health status of the AI service and Gemini AI availability",
    response_description="Service health status and Gemini AI availability",
    tags=["Health"],
    responses={
        200: {
            "description": "Service health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "chefassist-ai",
                        "version": "1.0.0",
                        "gemini_available": True
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the service and whether Gemini AI is
    properly configured and available.
    """
    from app.services.gemini_service import GeminiService
    gemini_service = GeminiService()
    
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.version,
        "gemini_available": gemini_service.is_available()
    }
