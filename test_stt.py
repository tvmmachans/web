#!/usr/bin/env python3
"""
Test script for Speech-to-Text functionality
Tests all available STT providers with Malayalam audio.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.speech_recognition import speech_recognition_service, STTProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_stt_providers():
    """Test all available STT providers."""
    print("🔍 Testing Speech-to-Text Providers")
    print("=" * 50)

    # Check available providers
    health = await speech_recognition_service.health_check()
    print("📊 Provider Status:")
    for provider, available in health.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {provider}: {status}")
    print()

    # Test with sample Malayalam text (if audio file exists)
    test_audio_path = "test_audio.wav"  # You would need to provide this

    if os.path.exists(test_audio_path):
        print("🎵 Testing with audio file...")
        with open(test_audio_path, 'rb') as f:
            audio_data = f.read()

        # Test each provider
        providers_to_test = [
            STTProvider.GOOGLE,
            STTProvider.AZURE,
            STTProvider.SPEECH_RECOGNITION
        ]

        for provider in providers_to_test:
            print(f"\n🔄 Testing {provider.value}...")
            try:
                result = await speech_recognition_service.transcribe_audio(
                    audio_data, language="ml-IN", providers=[provider]
                )

                if result.get("text"):
                    print(f"  ✅ Success: {result['text'][:100]}...")
                    print(f"  📊 Confidence: {result.get('confidence', 'N/A')}")
                else:
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

    else:
        print("⚠️  No test audio file found. Create 'test_audio.wav' to test transcription.")
        print("   You can record a short Malayalam audio clip for testing.")

    # Test language support
    print("\n🌍 Supported Languages:")
    languages = await speech_recognition_service.get_supported_languages()
    for provider, langs in languages.items():
        print(f"  {provider}: {', '.join(langs)}")


async def test_ai_service_integration():
    """Test integration with ai_service.py"""
    print("\n🔗 Testing AI Service Integration")
    print("=" * 50)

    try:
        from services.ai_service import transcribe_video, generate_subtitles_service

        # Test with a sample video (if exists)
        test_video_path = "test_video.mp4"

        if os.path.exists(test_video_path):
            print("🎬 Testing video transcription...")

            # Test transcription
            transcription = transcribe_video(test_video_path, language="ml")
            print(f"📝 Transcription: {transcription[:200]}...")

            # Test subtitles
            subtitles = await generate_subtitles_service(test_video_path, language="ml")
            print(f"🎭 Subtitles generated: {len(subtitles)} segments")

        else:
            print("⚠️  No test video file found. Create 'test_video.mp4' to test full pipeline.")

    except Exception as e:
        print(f"❌ AI Service integration failed: {str(e)}")


def main():
    """Main test function."""
    print("🧪 Speech-to-Text Testing Suite")
    print("This script tests the alternative STT implementations")
    print()

    # Run async tests
    asyncio.run(test_stt_providers())
    asyncio.run(test_ai_service_integration())

    print("\n✅ Testing complete!")
    print("\n💡 Tips:")
    print("  - Set up API keys in .env for cloud providers")
    print("  - Download Vosk models for offline transcription")
    print("  - Test with actual Malayalam audio for best results")


if __name__ == "__main__":
    main()
