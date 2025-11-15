"""
Alternative Speech Recognition Service
Provides multiple STT backends as alternatives to Whisper for Malayalam and other languages.
"""

import asyncio
import io
import logging
import os
import tempfile
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx
import numpy as np
from google.cloud import speech
from google.oauth2 import service_account
import azure.cognitiveservices.speech as speechsdk
import vosk
import speech_recognition as sr

logger = logging.getLogger(__name__)


class STTProvider(Enum):
    GOOGLE = "google"
    AZURE = "azure"
    VOSK = "vosk"
    SPEECH_RECOGNITION = "speech_recognition"


class SpeechRecognitionService:
    """
    Multi-provider speech recognition service with Malayalam support.
    Provides fallbacks when primary provider fails.
    """

    def __init__(self):
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available speech recognition providers."""
        # Google Cloud Speech-to-Text
        google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if google_creds_path and os.path.exists(google_creds_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    google_creds_path
                )
                self.providers[STTProvider.GOOGLE] = speech.SpeechClient(
                    credentials=credentials
                )
                logger.info("Google Speech-to-Text initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Speech: {e}")

        # Azure Speech Services
        azure_key = os.getenv("AZURE_SPEECH_KEY")
        azure_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        if azure_key:
            try:
                speech_config = speechsdk.SpeechConfig(
                    subscription=azure_key, region=azure_region
                )
                self.providers[STTProvider.AZURE] = speech_config
                logger.info("Azure Speech Services initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure Speech: {e}")

        # Vosk (offline)
        vosk_model_path = os.getenv("VOSK_MODEL_PATH")
        if vosk_model_path and os.path.exists(vosk_model_path):
            try:
                self.providers[STTProvider.VOSK] = vosk.Model(vosk_model_path)
                logger.info("Vosk model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Vosk: {e}")

        # SpeechRecognition library
        try:
            self.providers[STTProvider.SPEECH_RECOGNITION] = sr.Recognizer()
            logger.info("SpeechRecognition library initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize SpeechRecognition: {e}")

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "ml-IN",  # Malayalam (India)
        providers: Optional[List[STTProvider]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Transcribe audio using available providers with fallbacks.

        Args:
            audio_data: Raw audio bytes
            language: Language code (ml-IN for Malayalam, en-US for English)
            providers: List of providers to try (tries all if None)
            timeout: Timeout per provider in seconds

        Returns:
            Dict with transcription results and metadata
        """
        if providers is None:
            providers = list(self.providers.keys())

        results = []
        errors = []

        for provider in providers:
            if provider not in self.providers:
                continue

            try:
                logger.info(f"Trying {provider.value} for language {language}")
                result = await self._transcribe_with_provider(
                    provider, audio_data, language, timeout
                )
                if result.get("text"):
                    results.append(result)
                    # Return first successful result
                    return result
            except Exception as e:
                error_msg = f"{provider.value} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

        # If all providers failed, return error summary
        return {
            "text": "",
            "confidence": 0.0,
            "language": language,
            "provider": "none",
            "error": "All speech recognition providers failed",
            "errors": errors,
            "available_providers": list(self.providers.keys()),
        }

    async def _transcribe_with_provider(
        self, provider: STTProvider, audio_data: bytes, language: str, timeout: int
    ) -> Dict[str, Any]:
        """Transcribe using specific provider."""
        if provider == STTProvider.GOOGLE:
            return await self._google_transcribe(audio_data, language, timeout)
        elif provider == STTProvider.AZURE:
            return await self._azure_transcribe(audio_data, language, timeout)
        elif provider == STTProvider.VOSK:
            return await self._vosk_transcribe(audio_data, language, timeout)
        elif provider == STTProvider.SPEECH_RECOGNITION:
            return await self._speech_recognition_transcribe(
                audio_data, language, timeout
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _google_transcribe(
        self, audio_data: bytes, language: str, timeout: int
    ) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text."""
        client = self.providers[STTProvider.GOOGLE]

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )

        # Create audio object
        audio = speech.RecognitionAudio(content=audio_data)

        # Perform recognition
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.recognize(config=config, audio=audio)
        )

        if response.results:
            result = response.results[0]
            return {
                "text": result.alternatives[0].transcript,
                "confidence": result.alternatives[0].confidence,
                "language": language,
                "provider": "google",
                "segments": self._extract_segments_google(result),
            }

        return {
            "text": "",
            "confidence": 0.0,
            "language": language,
            "provider": "google",
        }

    async def _azure_transcribe(
        self, audio_data: bytes, language: str, timeout: int
    ) -> Dict[str, Any]:
        """Transcribe using Azure Speech Services."""
        speech_config = self.providers[STTProvider.AZURE]
        speech_config.speech_recognition_language = language

        # Create audio stream from bytes
        stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=stream)

        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Push audio data
        stream.write(audio_data)
        stream.close()

        # Perform recognition
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: recognizer.recognize_once()
        )

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {
                "text": result.text,
                "confidence": 0.8,  # Azure doesn't provide confidence easily
                "language": language,
                "provider": "azure",
            }

        return {
            "text": "",
            "confidence": 0.0,
            "language": language,
            "provider": "azure",
        }

    async def _vosk_transcribe(
        self, audio_data: bytes, language: str, timeout: int
    ) -> Dict[str, Any]:
        """Transcribe using Vosk (offline)."""
        model = self.providers[STTProvider.VOSK]

        # Create Kaldi recognizer
        rec = vosk.KaldiRecognizer(model, 16000)

        # Process audio in chunks
        results = []
        chunk_size = 4000

        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i : i + chunk_size]
            if rec.AcceptWaveform(chunk):
                result = rec.Result()
                results.append(result)

        # Final result
        final_result = rec.FinalResult()

        # Combine results
        full_text = ""
        for result in results:
            import json

            data = json.loads(result)
            full_text += data.get("text", "")

        final_data = json.loads(final_result)
        full_text += final_data.get("text", "")

        return {
            "text": full_text.strip(),
            "confidence": 0.7,  # Vosk doesn't provide confidence
            "language": language,
            "provider": "vosk",
        }

    async def _speech_recognition_transcribe(
        self, audio_data: bytes, language: str, timeout: int
    ) -> Dict[str, Any]:
        """Transcribe using SpeechRecognition library."""
        recognizer = self.providers[STTProvider.SPEECH_RECOGNITION]

        # Convert bytes to AudioData
        audio = sr.AudioData(audio_data, 16000, 2)  # 16kHz, 16-bit

        try:
            # Try Google Web Speech API (free, no key needed)
            text = await asyncio.get_event_loop().run_in_executor(
                None, lambda: recognizer.recognize_google(audio, language=language)
            )

            return {
                "text": text,
                "confidence": 0.6,  # Estimated confidence
                "language": language,
                "provider": "speech_recognition",
            }
        except sr.UnknownValueError:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "provider": "speech_recognition",
            }
        except sr.RequestError as e:
            raise Exception(f"Speech Recognition API error: {e}")

    def _extract_segments_google(self, result) -> List[Dict]:
        """Extract timing segments from Google Speech result."""
        segments = []
        if result.alternatives:
            for word in result.alternatives[0].words:
                segments.append(
                    {
                        "word": word.word,
                        "start_time": word.start_time.total_seconds(),
                        "end_time": word.end_time.total_seconds(),
                    }
                )
        return segments

    async def get_supported_languages(self) -> Dict[str, List[str]]:
        """Get supported languages for each provider."""
        return {
            "google": ["ml-IN", "en-US", "hi-IN", "ta-IN", "te-IN"],
            "azure": ["ml-IN", "en-US", "hi-IN", "ta-IN", "te-IN"],
            "vosk": ["en", "cn", "ru", "fr", "de"],  # Limited models available
            "speech_recognition": ["ml", "en", "hi", "ta", "te"],
        }

    async def health_check(self) -> Dict[str, bool]:
        """Check which providers are available and working."""
        health = {}
        for provider in STTProvider:
            health[provider.value] = provider in self.providers
        return health


# Global speech recognition service instance
speech_recognition_service = SpeechRecognitionService()
