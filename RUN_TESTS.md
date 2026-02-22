# Running Tests for AI Service

## Quick Start

### 1. Activate Virtual Environment

```bash
cd ai-service
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 2. Install/Update Dependencies (if needed)

```bash
pip install -r requirements.txt
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Or use python module syntax (works without activating venv)
python3 -m pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## Alternative: Use Python Module Syntax

If you don't want to activate the virtual environment, you can use:

```bash
cd ai-service
python3 -m pytest
```

This will use the pytest installed in your Python environment.

## Troubleshooting

### "pytest: command not found"

**Solution 1**: Activate virtual environment first
```bash
source venv/bin/activate
pytest
```

**Solution 2**: Use python module syntax
```bash
python3 -m pytest
```

**Solution 3**: Install pytest globally (not recommended)
```bash
pip3 install pytest pytest-asyncio pytest-mock pytest-cov
```

### "Module not found" errors

Make sure you're in the `ai-service` directory and dependencies are installed:
```bash
cd ai-service
source venv/bin/activate
pip install -r requirements.txt
```

### Virtual environment not working

Recreate the virtual environment:
```bash
cd ai-service
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
