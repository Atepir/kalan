# Ollama Setup Guide

## What is Ollama?

Ollama is a tool that allows you to run large language models locally on your machine. This means:
- ✅ **No API costs** - Run models completely free
- ✅ **Privacy** - Your data never leaves your machine
- ✅ **Offline capable** - Works without internet connection
- ✅ **Multiple models** - Choose from Llama, Mistral, CodeLlama, and more

## Quick Start with Docker

The easiest way to use Ollama with this project is via Docker (already configured):

```powershell
# Start all services including Ollama
docker-compose up -d

# Pull your first model (this downloads ~4-5GB)
docker exec -it research-collective-ollama ollama pull llama3.1:8b

# Verify it's working
docker exec -it research-collective-ollama ollama list
```

## Available Models

### Recommended Models

| Model | Size | RAM Required | Best For |
|-------|------|--------------|----------|
| **llama3.1:8b** | 4.7GB | 8GB | General purpose, good balance |
| **mistral:7b** | 4.1GB | 8GB | Fast, efficient responses |
| **phi3:mini** | 2.3GB | 4GB | Lightweight, quick responses |
| **codellama:13b** | 7.4GB | 16GB | Code generation and analysis |
| **llama3.1:70b** | 40GB | 64GB | Best quality (requires GPU) |

### Pull Additional Models

```powershell
# Fast, lightweight model for testing
docker exec -it research-collective-ollama ollama pull phi3:mini

# Better for code-related tasks
docker exec -it research-collective-ollama ollama pull codellama:13b

# Excellent general-purpose model
docker exec -it research-collective-ollama ollama pull mistral:7b
```

## Switching Models

Update your `.env` file:

```bash
# For fastest responses (good for testing)
OLLAMA_MODEL=phi3:mini

# For balanced performance (recommended)
OLLAMA_MODEL=llama3.1:8b

# For best quality responses
OLLAMA_MODEL=mistral:7b

# For code-heavy tasks
OLLAMA_MODEL=codellama:13b
```

Then restart your application to use the new model.

## GPU Acceleration (Optional)

### NVIDIA GPU

If you have an NVIDIA GPU, the docker-compose.yml is already configured to use it. Just make sure you have:

1. **NVIDIA Docker runtime installed**:
   ```powershell
   # Install NVIDIA Container Toolkit
   # Follow: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
   ```

2. **Verify GPU is detected**:
   ```powershell
   docker exec -it research-collective-ollama nvidia-smi
   ```

### CPU Only

If you don't have a GPU, Ollama will run on CPU. This is slower but works fine for smaller models:

```yaml
# Edit docker-compose.yml and remove the deploy section under ollama:
  ollama:
    image: ollama/ollama:latest
    # ... other config ...
    # Remove or comment out the deploy section
```

## Testing Ollama

### Test from Command Line

```powershell
# Simple test
docker exec -it research-collective-ollama ollama run llama3.1:8b "What is machine learning?"

# Check available models
docker exec -it research-collective-ollama ollama list
```

### Test from Python

Create a test file `test_ollama.py`:

```python
import asyncio
from src.llm.client import get_ollama_client

async def test():
    client = get_ollama_client()
    response = await client.generate(
        prompt="Explain neural networks in 2 sentences.",
        system="You are a helpful AI assistant."
    )
    print(response["content"])
    await client.close()

asyncio.run(test())
```

Run it:
```powershell
poetry run python test_ollama.py
```

## Performance Tips

### 1. Model Size vs Speed

- **Smaller models (7B-8B)**: Fast, good for most tasks
- **Medium models (13B-30B)**: Slower but better quality
- **Large models (70B+)**: Requires GPU, best quality

### 2. Optimize for Your Hardware

**Low RAM (8GB or less)**:
```bash
OLLAMA_MODEL=phi3:mini
```

**Medium RAM (16GB)**:
```bash
OLLAMA_MODEL=llama3.1:8b
```

**High RAM (32GB+) or GPU**:
```bash
OLLAMA_MODEL=llama3.1:70b
```

### 3. Concurrent Requests

Adjust in `.env` based on your hardware:

```bash
# Conservative (for 8GB RAM)
MAX_CONCURRENT_AGENTS=2

# Moderate (for 16GB RAM)
MAX_CONCURRENT_AGENTS=5

# Aggressive (for 32GB+ RAM with GPU)
MAX_CONCURRENT_AGENTS=10
```

## Troubleshooting

### Issue: Model download fails

```powershell
# Check internet connection and retry
docker exec -it research-collective-ollama ollama pull llama3.1:8b

# Or download a smaller model first
docker exec -it research-collective-ollama ollama pull phi3:mini
```

### Issue: Out of memory errors

```powershell
# Switch to a smaller model
docker exec -it research-collective-ollama ollama pull phi3:mini

# Update .env
# OLLAMA_MODEL=phi3:mini

# Restart application
```

### Issue: Slow responses

```powershell
# Use a smaller model
OLLAMA_MODEL=phi3:mini

# Reduce concurrent agents
MAX_CONCURRENT_AGENTS=2

# Enable GPU if available (see GPU section above)
```

### Issue: Connection refused

```powershell
# Check if Ollama is running
docker ps | findstr ollama

# Restart Ollama container
docker-compose restart ollama

# Check logs
docker-compose logs ollama
```

## Model Management

### List Downloaded Models

```powershell
docker exec -it research-collective-ollama ollama list
```

### Remove Unused Models

```powershell
# Free up disk space by removing models you don't use
docker exec -it research-collective-ollama ollama rm llama3.1:70b
```

### Update Models

```powershell
# Re-pull to get the latest version
docker exec -it research-collective-ollama ollama pull llama3.1:8b
```

## API Compatibility

The Ollama client in this project maintains compatibility with the previous Anthropic Claude interface, so existing code continues to work:

```python
# Both work the same way
from src.llm.client import get_ollama_client, get_claude_client

client = get_ollama_client()  # New way
# client = get_claude_client()  # Old way (alias)
```

## Advanced Configuration

### Custom Ollama Server

If running Ollama outside Docker:

```bash
# In .env
OLLAMA_BASE_URL=http://your-ollama-server:11434
```

### Model Parameters

You can customize model behavior:

```python
response = await client.generate(
    prompt="Your prompt",
    temperature=0.7,  # Lower = more focused, Higher = more creative
    max_tokens=4096,  # Maximum response length
    stop_sequences=["###", "END"]  # Custom stop sequences
)
```

## Resources

- **Ollama Documentation**: https://ollama.ai/
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **Discord Community**: https://discord.gg/ollama

## Comparison: Ollama vs. Cloud APIs

| Feature | Ollama (Local) | Cloud APIs |
|---------|---------------|------------|
| Cost | Free | $0.01-0.30 per 1K tokens |
| Privacy | Complete | Data sent to provider |
| Speed | Depends on hardware | Usually fast |
| Setup | Pull models (5-40GB) | Just API key |
| Offline | Yes | No |
| Models | Open-source only | Proprietary + open |
| Scaling | Limited by hardware | Virtually unlimited |

---

**Ready to start?** Run `docker-compose up -d` and pull your first model! 🚀
