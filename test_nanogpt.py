#!/usr/bin/env python3
"""
Simple test script for Nano-GPT integration.
Run this after adding your API key to backend/.env
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment from backend/.env
backend_path = Path(__file__).parent / "backend"
env_path = backend_path / ".env"
load_dotenv(env_path)

# Add backend to path so we can import
sys.path.insert(0, str(backend_path))

from app.services.llm_manager import LLMManager, LLMProvider, ChatMessage
from app.config import config

async def test_nanogpt():
    """Test Nano-GPT API integration."""
    print("🧪 Testing Nano-GPT Integration")
    print("=" * 40)

    # Check if API key is configured
    if not config.llm.nano_gpt_api_key:
        print("❌ NANO_GPT_API_KEY not found in environment")
        print("📝 Please add your API key to backend/.env:")
        print("   NANO_GPT_API_KEY=your_actual_api_key_here")
        return False

    print(f"✅ API key configured: {config.llm.nano_gpt_api_key[:8]}...")
    print(f"🌐 Base URL: {config.llm.nano_gpt_base_url}")

    # Initialize LLM manager
    llm_manager = LLMManager()

    # Get available models
    print("\n🔍 Getting available models...")
    models = await llm_manager.get_available_models()
    nano_gpt_models = [m for m in models.values() if m.provider == LLMProvider.NANO_GPT]
    if nano_gpt_models:
        print(f"✅ Found {len(nano_gpt_models)} Nano-GPT models:")
        for model in nano_gpt_models[:3]:  # Show first 3
            print(f"   - {model.id}: {model.name}")
    else:
        print("⚠️  No Nano-GPT models configured, using default")

    # Test simple completion
    print("\n💬 Testing simple completion...")
    messages = [
        ChatMessage(role="user", content="Hello! Please respond with 'Hello from Nano-GPT!'")
    ]

    try:
        # Set to a Nano-GPT model first
        await llm_manager.set_model("gpt-4o-mini")  # Using Nano-GPT model
        response = await llm_manager.chat_completion(messages, temperature=0.7)

        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        else:
            print(f"✅ Success! Response: {response.content}")
            print(f"📊 Model: {response.model}")
            print(f"🎯 Tokens used: {response.tokens_used}")
            return True

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    """Main test function."""
    success = await test_nanogpt()

    if success:
        print("\n🎉 Nano-GPT integration test passed!")
        print("🚀 Ready to use Nano-GPT in DeskMate")
    else:
        print("\n❌ Nano-GPT integration test failed")
        print("🔧 Check your API key and network connection")

    return success

if __name__ == "__main__":
    asyncio.run(main())