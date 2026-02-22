# Ollama Setup Guide for ChefAssist AI Service

## Overview

The ChefAssist AI service uses **Ollama** for local AI model inference. Ollama allows you to run large language models (LLMs) locally on your machine.

## Quick Start

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
# Or download from https://ollama.ai/download
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

### 2. Start Ollama Server

```bash
ollama serve
```

This starts Ollama on `http://localhost:11434` (default port).

### 3. Install Required Models

For **ingredient recognition** (vision), you need a vision model:
```bash
ollama pull llava
# Or
ollama pull bakllava
# Or
ollama pull moondream
```

For **recipe generation** (text), you need a text model:
```bash
ollama pull llama2
# Or
ollama pull mistral
# Or
ollama pull phi
# Or any other text generation model
```

### 4. Configure the AI Service

Update `ai-service/.env`:

```env
# For vision (ingredient recognition)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llava

# For text generation (recipe suggestions)
# You might want to use a different model for text
# OLLAMA_MODEL=llama2  # or mistral, phi, etc.
```

## Important Notes

### Model Types

- **Vision Models** (`llava`, `bakllava`, `moondream`): For ingredient recognition from images
- **Text Models** (`llama2`, `mistral`, `phi`, etc.): For recipe generation and suggestions

**Current Issue**: The service is configured to use `llava` (a vision model) for both vision AND text generation. This might cause issues.

### Recommended Configuration

For best results, you might want to:

1. **Use `llava` for vision** (ingredient recognition)
2. **Use a text model** (like `llama2` or `mistral`) for recipe generation

However, the current implementation uses the same model for both. If you're getting errors with text generation, try:

```bash
# Install a text model
ollama pull llama2

# Update .env
OLLAMA_MODEL=llama2
```

### Troubleshooting

#### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check if it's on the correct port: `curl http://localhost:11434/api/tags`

#### "Model not found"
- List installed models: `ollama list`
- Install the model: `ollama pull <model-name>`

#### "Server disconnected without sending a response"
- This usually means Ollama crashed or ran out of memory
- Try a smaller model or increase system resources
- Check Ollama logs for errors

#### "Request timed out"
- Local models can be slow (especially on CPU)
- Increase timeout in `.env`: `OLLAMA_TIMEOUT=300` (5 minutes)
- Consider using a smaller/faster model

### Testing Ollama

Test if Ollama is working:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test text generation
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello, how are you?",
  "stream": false
}'

# Test vision (if you have llava)
curl http://localhost:11434/api/generate -d '{
  "model": "llava",
  "prompt": "What is in this image?",
  "images": ["<base64_image>"],
  "stream": false
}'
```

## Current Configuration

The service is configured to use:
- **URL**: `http://localhost:11434` (default Ollama port)
- **Model**: `llava` (vision model)
- **Timeout**: 300 seconds (5 minutes) for local models
- **Retries**: 2 attempts

## Next Steps

1. **Start Ollama**: `ollama serve`
2. **Install models**: `ollama pull llava` (and optionally a text model)
3. **Restart FastAPI service** to pick up changes
4. **Test the endpoints** to verify everything works
