# Ollama Quick Reference

## Basic Usage

```python
from src.llm.client import get_ollama_client
import asyncio

async def main():
    client = get_ollama_client()
    
    # Simple generation
    response = await client.generate(
        prompt="Explain machine learning",
        system="You are a helpful teacher"
    )
    print(response["content"])
    
    await client.close()

asyncio.run(main())
```

## Common Commands

```powershell
# List available models
docker exec -it research-collective-ollama ollama list

# Pull a new model
docker exec -it research-collective-ollama ollama pull llama3.1:8b

# Remove a model
docker exec -it research-collective-ollama ollama rm llama3.1:70b

# Test a model interactively
docker exec -it research-collective-ollama ollama run llama3.1:8b
```

## Client Methods

```python
# Basic generation
response = await client.generate(
    prompt="Your question",
    system="System prompt",
    temperature=0.7,
    max_tokens=4096,
    stop_sequences=["###"]
)

# With tools/functions
response = await client.generate_with_tools(
    prompt="Your question",
    tools=[{"name": "search", "description": "Search the web"}],
    system="You are helpful"
)

# Batch generation
responses = await client.batch_generate(
    prompts=["Q1", "Q2", "Q3"],
    max_concurrent=3
)

# List available models
models = await client.list_models()

# Pull a new model
success = await client.pull_model("mistral:7b")

# Get usage stats
stats = client.get_usage_stats()
```

## Response Format

```python
{
    "content": "Generated text response",
    "usage": {
        "input_tokens": 15,
        "output_tokens": 128,
        "total_tokens": 143
    },
    "model": "llama3.1:8b",
    "stop_reason": "stop",  # or "length"
    "request_id": "req_42"
}
```

## Model Selection Guide

```python
# For speed (testing/development)
OLLAMA_MODEL=phi3:mini

# For balanced performance (recommended)
OLLAMA_MODEL=llama3.1:8b

# For quality
OLLAMA_MODEL=mistral:7b

# For code tasks
OLLAMA_MODEL=codellama:13b
```

## Configuration (.env)

```bash
# Ollama server URL
OLLAMA_BASE_URL=http://localhost:11434

# Model to use
OLLAMA_MODEL=llama3.1:8b

# Max tokens per response
OLLAMA_MAX_TOKENS=4096

# Concurrency control
MAX_CONCURRENT_AGENTS=5
MAX_REQUESTS_PER_MINUTE=50
```

## Docker Management

```powershell
# Start Ollama
docker-compose up -d ollama

# Stop Ollama
docker-compose stop ollama

# View logs
docker-compose logs -f ollama

# Restart Ollama
docker-compose restart ollama

# Remove Ollama (keeps models)
docker-compose down ollama

# Remove everything including models
docker-compose down -v
```

## Monitoring

```python
# Check token usage
stats = client.get_usage_stats()
print(f"Requests: {stats['total_requests']}")
print(f"Tokens: {stats['total_tokens_used']}")

# Log each request (automatic)
# Logs go to console and logs/ directory
```

## Performance Tuning

```python
# Adjust temperature (0.0-1.0)
# Lower = more focused, Higher = more creative
response = await client.generate(
    prompt="...",
    temperature=0.3  # More deterministic
)

# Limit response length
response = await client.generate(
    prompt="...",
    max_tokens=500  # Shorter response
)

# Use stop sequences
response = await client.generate(
    prompt="...",
    stop_sequences=["###", "\n\n"]
)
```

## Error Handling

```python
import httpx

try:
    response = await client.generate(prompt="Hello")
except httpx.TimeoutException:
    print("Request timed out")
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
except Exception as e:
    print(f"Error: {e}")
```

## Testing

```python
# Unit test example
import pytest
from src.llm.client import OllamaClient

@pytest.mark.asyncio
async def test_generation():
    client = OllamaClient()
    response = await client.generate("Say hello")
    assert "content" in response
    assert len(response["content"]) > 0
    await client.close()
```

## Troubleshooting

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test model directly
docker exec -it research-collective-ollama ollama run llama3.1:8b "Hello"

# View Ollama logs
docker logs research-collective-ollama

# Check available disk space (models are large!)
docker exec -it research-collective-ollama df -h
```

## Advanced: Custom Ollama Server

```python
# Connect to remote Ollama server
from src.llm.client import OllamaClient

client = OllamaClient(
    base_url="http://192.168.1.100:11434",
    model="llama3.1:8b"
)
```

## Model Comparison

| Model | Speed | Quality | Memory | Best For |
|-------|-------|---------|--------|----------|
| phi3:mini | ⚡⚡⚡ | ⭐⭐ | 4GB | Testing |
| llama3.1:8b | ⚡⚡ | ⭐⭐⭐ | 8GB | General |
| mistral:7b | ⚡⚡ | ⭐⭐⭐⭐ | 8GB | Quality |
| codellama:13b | ⚡ | ⭐⭐⭐ | 16GB | Code |
| llama3.1:70b | 🐌 | ⭐⭐⭐⭐⭐ | 64GB | Best |

## Quick Tips

1. **Start small**: Test with `phi3:mini` before using larger models
2. **Monitor memory**: Use Task Manager to watch RAM usage
3. **Use GPU**: Dramatically faster with NVIDIA GPU
4. **Cache models**: Models persist between container restarts
5. **Batch requests**: More efficient than sequential calls

## Links

- 📚 [Full Ollama Setup Guide](OLLAMA_SETUP.md)
- 📖 [Migration Guide](MIGRATION_TO_OLLAMA.md)
- 🏠 [Project README](README.md)
