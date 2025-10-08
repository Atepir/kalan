"""
Simple test script to verify Ollama integration works.

Run with: poetry run python test_ollama_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm.client import get_ollama_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_basic_generation():
    """Test basic text generation."""
    print("=" * 60)
    print("TEST 1: Basic Text Generation")
    print("=" * 60)
    
    try:
        client = get_ollama_client()
        
        response = await client.generate(
            prompt="What is 2+2? Answer in one sentence.",
            system="You are a helpful math teacher.",
            temperature=0.3,
        )
        
        print(f"✅ SUCCESS")
        print(f"Model: {response['model']}")
        print(f"Tokens: {response['usage']['total_tokens']}")
        print(f"Response: {response['content'][:200]}")
        print()
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_with_system_prompt():
    """Test generation with system prompt."""
    print("=" * 60)
    print("TEST 2: Generation with System Prompt")
    print("=" * 60)
    
    try:
        client = get_ollama_client()
        
        response = await client.generate(
            prompt="Explain neural networks",
            system="You are a computer science professor. Keep explanations brief.",
            max_tokens=150,
        )
        
        print(f"✅ SUCCESS")
        print(f"Response length: {len(response['content'])} chars")
        print(f"Response preview: {response['content'][:150]}...")
        print()
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_batch_generation():
    """Test batch generation."""
    print("=" * 60)
    print("TEST 3: Batch Generation")
    print("=" * 60)
    
    try:
        client = get_ollama_client()
        
        prompts = [
            "What is Python?",
            "What is JavaScript?",
            "What is Rust?",
        ]
        
        responses = await client.batch_generate(
            prompts=prompts,
            system="Answer in one sentence.",
            max_concurrent=2,
        )
        
        print(f"✅ SUCCESS")
        print(f"Generated {len(responses)} responses")
        for i, resp in enumerate(responses, 1):
            print(f"  {i}. {resp['content'][:80]}...")
        print()
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_model_listing():
    """Test listing available models."""
    print("=" * 60)
    print("TEST 4: List Available Models")
    print("=" * 60)
    
    try:
        client = get_ollama_client()
        
        models = await client.list_models()
        
        print(f"✅ SUCCESS")
        print(f"Found {len(models)} models:")
        for model in models:
            name = model.get("name", "unknown")
            size = model.get("size", 0) / (1024**3)  # Convert to GB
            print(f"  - {name} ({size:.1f} GB)")
        print()
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_usage_stats():
    """Test usage statistics tracking."""
    print("=" * 60)
    print("TEST 5: Usage Statistics")
    print("=" * 60)
    
    try:
        client = get_ollama_client()
        
        # Make a few requests
        for i in range(3):
            await client.generate(f"Count to {i+1}")
        
        stats = client.get_usage_stats()
        
        print(f"✅ SUCCESS")
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total tokens: {stats['total_tokens_used']}")
        print(f"Model: {stats['model']}")
        print()
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OLLAMA INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Basic Generation", test_basic_generation),
        ("System Prompt", test_with_system_prompt),
        ("Batch Generation", test_batch_generation),
        ("Model Listing", test_model_listing),
        ("Usage Stats", test_usage_stats),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ollama integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check Ollama setup:")
        print("  1. Is Ollama running? (docker-compose ps)")
        print("  2. Is a model pulled? (docker exec -it research-collective-ollama ollama list)")
        print("  3. Check logs: (docker-compose logs ollama)")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
