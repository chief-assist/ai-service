# API Key Setup Guide

## What is the X-API-Key?

The `X-API-Key` is a **shared secret** used to authenticate requests between your Express API (backend) and the FastAPI AI Service. It's a simple security measure to prevent unauthorized access to your AI service.

## How to Get/Set the API Key

### Step 1: Generate an API Key

You can use any secure random string as your API key. Here are some options:

**Option A: Use a simple password**
```bash
# Example: Esther123!@#
```

**Option B: Generate a secure random key**
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -hex 32

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Step 2: Set in FastAPI Service

Add the API key to your `.env` file in the `ai-service` directory:

```env
API_KEY=your_generated_api_key_here
```

**Example:**
```env
API_KEY=Esther123!@#
```

### Step 3: Set in Express API

Add the same API key to your Express API `.env` file:

```env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=your_generated_api_key_here
```

**Example:**
```env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=Esther123!@#
```

### Step 4: Use in Express API Code

When making requests to the FastAPI service, include the API key in the headers:

```javascript
// In your Express API routes (e.g., backend/routes/ingredients.js)
const axios = require('axios');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
const AI_SERVICE_API_KEY = process.env.AI_SERVICE_API_KEY;

async function recognizeIngredients(req, res) {
  try {
    const { image_url, image_base64 } = req.body;
    
    // Forward to AI service with API key
    const response = await axios.post(
      `${AI_SERVICE_URL}/api/ai/recognize-ingredients`,
      { image_url, image_base64 },
      {
        headers: {
          'X-API-Key': AI_SERVICE_API_KEY
        }
      }
    );
    
    res.json(response.data);
  } catch (error) {
    console.error('AI service error:', error.response?.data || error.message);
    res.status(500).json({ error: 'AI service unavailable' });
  }
}
```

## Testing the API Key

### Using Swagger UI

1. Start the FastAPI service:
   ```bash
   cd ai-service
   uvicorn app.main:app --reload --port 8000
   ```

2. Open Swagger UI: `http://localhost:8000/docs`

3. Click the **"Authorize"** button at the top right

4. Enter your API key in the `ApiKeyAuth` field:
   ```
   Esther123!@#
   ```

5. Click **"Authorize"** and then **"Close"**

6. Now you can test endpoints - they will automatically include the X-API-Key header

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/ai/recognize-ingredients" \
  -H "X-API-Key: Esther123!@#" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg"
  }'
```

### Using Postman

1. Create a new request
2. Set the URL: `POST http://localhost:8000/api/ai/recognize-ingredients`
3. Go to **Headers** tab
4. Add header:
   - Key: `X-API-Key`
   - Value: `Esther123!@#`
5. Add body with JSON data
6. Send request

## Development Mode

If you don't set `API_KEY` in your `.env` file, the service will run in **development mode** and allow all requests without authentication. This is convenient for local development but **NOT recommended for production**.

You'll see a warning in the logs:
```
WARNING: API key not configured - allowing all requests
```

## Security Best Practices

1. **Never commit API keys to git** - They should be in `.env` files (which are in `.gitignore`)

2. **Use different keys for different environments:**
   - Development: `dev-api-key-123`
   - Staging: `staging-api-key-456`
   - Production: Generate a strong random key

3. **Rotate keys periodically** - If a key is compromised, generate a new one

4. **Use strong keys in production** - At least 32 characters, mix of letters, numbers, and symbols

## Troubleshooting

### Error: "API key required"
- Make sure you're sending the `X-API-Key` header
- Check that the header name is exactly `X-API-Key` (case-sensitive)

### Error: "Invalid API key"
- Verify the API key in your `.env` file matches what you're sending
- Make sure there are no extra spaces or newlines in the key
- Restart the FastAPI service after changing `.env`

### Service allows all requests
- Check if `API_KEY` is set in your `.env` file
- If it's empty, the service runs in development mode
- Set a value to enable authentication
