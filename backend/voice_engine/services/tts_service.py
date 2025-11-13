import os
import torch
from TTS.api import TTS
from typing import Optional, Dict, Any
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import librosa
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.models = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"TTS Service initialized with device: {self.device}")

    async def load_model(self, model_name: str = "tts_models/ml/cv/vakyansh/wav2vec2-malayalam"):
        """Load TTS model asynchronously"""
        if model_name in self.models:
            return self.models[model_name]

        try:
            loop = asyncio.get_event_loop()
            tts = await loop.run_in_executor(
                self.executor,
                lambda: TTS(model_name).to(self.device)
            )
            self.models[model_name] = tts
            logger.info(f"Loaded TTS model: {model_name}")
            return tts
        except Exception as e:
            logger.error(f"Failed to load TTS model {model_name}: {e}")
            raise

    async def generate_speech(
        self,
        text: str,
        voice_profile: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate speech from text"""
        try:
            # Use Malayalam model by default
            model_name = "tts_models/ml/cv/vakyansh/wav2vec2-malayalam"
            tts = await self.load_model(model_name)

            # Apply settings
            emotion = settings.get('emotion', 'neutral') if settings else 'neutral'
            speed = settings.get('speed', 1.0) if settings else 1.0
            pitch = settings.get('pitch', 1.0) if settings else 1.0

            # Generate speech
            loop = asyncio.get_event_loop()
            wav = await loop.run_in_executor(
                self.executor,
                lambda: tts.tts(text=text, emotion=emotion)
            )

            # Apply speed and pitch modifications if needed
            if speed != 1.0 or pitch != 1.0:
                wav = self._modify_audio(wav, speed, pitch)

            # Convert to bytes
            import io
            buffer = io.BytesIO()
            sf.write(buffer, np.array(wav), 22050, format='wav')
            buffer.seek(0)
            return buffer.read()

        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise

    def _modify_audio(self, wav: np.ndarray, speed: float, pitch: float) -> np.ndarray:
        """Modify audio speed and pitch"""
        try:
            # Apply speed change
            if speed != 1.0:
                wav = librosa.effects.time_stretch(wav, rate=speed)

            # Apply pitch change
            if pitch != 1.0:
                wav = librosa.effects.pitch_shift(wav, sr=22050, n_steps=pitch*2)

            return wav
        except Exception as e:
            logger.warning(f"Audio modification failed: {e}")
            return wav

    async def get_available_models(self) -> Dict[str, Any]:
        """Get list of available TTS models"""
        return {
            "malayalam": "tts_models/ml/cv/vakyansh/wav2vec2-malayalam",
            "english": "tts_models/en/ljspeech/tacotron2-DDC_ph",
            "hindi": "tts_models/hi/cv/vakyansh/wav2vec2-hindi"
        }

    async def analyze_voice_quality(self, audio_path: str) -> Dict[str, float]:
        """Analyze voice quality metrics"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path)

            # Calculate metrics
            rms = librosa.feature.rms(y=y)[0]
            mean_rms = np.mean(rms)

            # Zero crossing rate (voice stability)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            mean_zcr = np.mean(zcr)

            # Spectral centroid (brightness)
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            mean_centroid = np.mean(centroid)

            # SNR estimation
            noise = np.mean(np.abs(y[np.abs(y) < 0.01]))
            signal = np.mean(np.abs(y))
            snr = 20 * np.log10(signal / (noise + 1e-10)) if noise > 0 else 60

            return {
                "volume": float(mean_rms),
                "stability": float(1.0 - mean_zcr),  # Lower ZCR = more stable
                "brightness": float(mean_centroid / 1000),  # kHz
                "snr": float(snr),
                "overall_quality": float((mean_rms * 0.3 + (1.0 - mean_zcr) * 0.3 + min(snr/60, 1.0) * 0.4))
            }

        except Exception as e:
            logger.error(f"Voice quality analysis failed: {e}")
            return {"error": str(e)}

# Global TTS service instance
tts_service = TTSService()
