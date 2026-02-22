# ChefAssist AI Service

FastAPI microservice for AI/ML operations including ingredient recognition and recipe generation using Google Gemini AI.

## Overview

This service handles all AI operations for ChefAssist:
- Ingredient recognition from images
- Recipe suggestions based on ingredients
- Recipe details generation
- Personalized recipe recommendations

## Technology Stack

- **FastAPI** - Modern Python web framework
- **Google Gemini AI** - LLM for recipe generation and ingredient recognition
- **Pillow** - Image processing
- **Pydantic** - Data validation

## Project Structure

```
ai-service/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── Dockerfile             # Container configuration
├── README.md              # This file
│
└── app/
    ├── main.py            # FastAPI app initialization
    ├── config.py          # Configuration settings
    ├── api/               # API routes
    ├── services/          # Business logic
    ├── models/            # Pydantic schemas
    ├── utils/             # Utility functions
    └── middleware/        # Request middleware
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `GOOGLE_API_KEY` or `GOOGLE_GENERATIVE_AI_API_KEY` - Gemini AI API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- `API_KEY` - **Service API key** - This is the X-API-Key value you'll use in requests

### About the API Key

The `API_KEY` is a **shared secret** between your Express API and this FastAPI service. It's used to authenticate requests from the Express API to the AI service.

**How to set it up:**

1. **Generate a secure API key** (any random string, e.g., `Esther123!@#` or use a generator)
2. **Set it in FastAPI `.env` file:**
   ```env
   API_KEY=your_secure_api_key_here
   ```

3. **Use the same key in Express API** when making requests:
   ```javascript
   const response = await axios.post(
     `${AI_SERVICE_URL}/api/ai/recognize-ingredients`,
     { image_url, image_base64 },
     {
       headers: {
         'X-API-Key': process.env.AI_SERVICE_API_KEY  // Same value as API_KEY
       }
     }
   );
   ```

4. **For testing in Swagger UI:**
   - Click the "Authorize" button at the top
   - Enter your `API_KEY` value
   - All requests will include the X-API-Key header

**Note:** If `API_KEY` is not set in `.env`, the service runs in development mode and allows all requests (not recommended for production).

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Or use the main.py entry point:
```bash
python main.py
```

## API Endpoints

### Base URL
```
http://localhost:8000/api/ai
```

### Endpoints

- `POST /api/ai/recognize-ingredients` - Recognize ingredients from image
- `POST /api/ai/suggest-recipes` - Get recipe suggestions
- `POST /api/ai/generate-recipe-details` - Generate recipe details
- `POST /api/ai/personalize-suggestions` - Get personalized suggestions
- `GET /api/ai/health` - Health check

See `docs/7ai.md` for complete API documentation.

## Integration

This service is called by the Express API (Port 5000). The Express API forwards AI requests to this service.

**Communication Flow:**
```
Client → Express API (5000) → FastAPI AI Service (8000) → Gemini AI
```

## Docker

### Build Image
```bash
docker build -t chefassist-ai .
```

### Run Container
```bash
docker run -p 8000:8000 --env-file .env chefassist-ai
```

## Deployment

For deployment options (especially for China), see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Recommended Free Hosting:**
- **Railway.app** - Easy setup, good China access, $5/month free credit
- **Render.com** - 750 hours/month free, good China access
- **Hugging Face Spaces** - Unlimited free tier, great for AI services
- **Aliyun/Tencent Cloud** - Best China performance (1 month free trial)

## Development

### Testing
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

## Environment Variables

See `.env.example` for all available environment variables.

## Documentation

- See `docs/7ai.md` for complete service documentation
- See `docs/9architecture.md` for architecture overview
- See `docs/6backend.md` for Express API integration

## License

Part of the ChefAssist project.
