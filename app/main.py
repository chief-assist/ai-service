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

logger = logging.getLogger(__name__)

# Initialize FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title="ChefAssist AI Service",
    description="""
    ## AI/ML Microservice for ChefAssist
    
    This service provides AI-powered capabilities for the ChefAssist application:
    
    * **Ingredient Recognition**: Identify ingredients from images using Ollama AI (local models)
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

# Request logging middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"[REQUEST] {request.method} {request.url.path}")
        logger.info(f"[REQUEST] Query params: {dict(request.query_params)}")
        
        # Extract and log API key header (partial for security)
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            api_key_preview = f"{api_key_header[:10]}...{api_key_header[-4:]}" if len(api_key_header) > 14 else api_key_header[:10] + "..."
            logger.info(f"[REQUEST] ✅ X-API-Key header: {api_key_preview} (length: {len(api_key_header)})")
        else:
            logger.warning("[REQUEST] ⚠️  X-API-Key header is MISSING")
        
        # Log other important headers
        content_type = request.headers.get("Content-Type", "N/A")
        logger.info(f"[REQUEST] Content-Type: {content_type}")
        logger.info(f"[REQUEST] All headers: {dict(request.headers)}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response

app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (enabled)
app.add_middleware(RateLimitMiddleware)

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
    description="Check the health status of the AI service and Ollama AI availability",
    response_description="Service health status and Ollama AI availability",
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
                        "ollama_available": True
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the service and whether Ollama AI is
    properly configured and available.
    """
    from app.services.ollama_service import OllamaService
    ollama_service = OllamaService()
    
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.version,
        "ollama_available": ollama_service.is_available()
    }
