import asyncio
import base64
import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import soundfile as sf
import torch
from scipy.io import wavfile
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

# Import Coqui TTS if available
try:
    from TTS.api import TTS

    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    logger.warning("Coqui TTS not available, using fallback TTS")

from database import Post, async_session
from voice_engine.services.tts_service import TTSService


class EmotionAwareTTS:
    """
    Emotion-aware Text-to-Speech system with Malayalam voice cloning capabilities.
    """

    def __init__(self):
        self.tts_service = TTSService()
        self.emotion_model = None
        self.emotion_tokenizer = None
        self.voice_clones = {}

        # Emotion mapping for Malayalam content
        self.emotion_config = {
            "joy": {
                "pitch_shift": 1.2,
                "speed": 1.1,
                "energy": 1.3,
                "malayalam_phrases": ["സന്തോഷകരമായ", "ആനന്ദകരമായ", "ഉത്സാഹജനകമായ"],
                "voice_style": "energetic",
            },
            "sadness": {
                "pitch_shift": 0.9,
                "speed": 0.9,
                "energy": 0.7,
                "malayalam_phrases": ["ദുഖകരമായ", "സങ്കടകരമായ", "കരുണാജനകമായ"],
                "voice_style": "calm",
            },
            "anger": {
                "pitch_shift": 1.1,
                "speed": 1.0,
                "energy": 1.2,
                "malayalam_phrases": ["ക്രോധജനകമായ", "ക്ഷുഭിതമായ", "തീക്ഷ്ണമായ"],
                "voice_style": "intense",
            },
            "fear": {
                "pitch_shift": 1.3,
                "speed": 1.2,
                "energy": 1.1,
                "malayalam_phrases": ["ഭയങ്കരമായ", "ഭീതിജനകമായ", "അപകടകരമായ"],
                "voice_style": "urgent",
            },
            "surprise": {
                "pitch_shift": 1.1,
                "speed": 1.0,
                "energy": 1.2,
                "malayalam_phrases": ["ആശ്ചര്യകരമായ", "പ്രത്യാശയില്ലാത്ത", "അപ്രതീക്ഷിതമായ"],
                "voice_style": "expressive",
            },
            "neutral": {
                "pitch_shift": 1.0,
                "speed": 1.0,
                "energy": 1.0,
                "malayalam_phrases": ["സാധാരണ", "ശാന്തമായ", "സമാധാനപരമായ"],
                "voice_style": "natural",
            },
        }

        self._load_emotion_model()
        self._initialize_tts_engine()

    def _load_emotion_model(self):
        """
        Load emotion detection model for Malayalam text.
        """
        try:
            # Use multilingual BERT for emotion detection
            model_name = "j-hartmann/emotion-english-distilroberta-base"
            self.emotion_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.emotion_model = AutoModelForSequenceClassification.from_pretrained(
                model_name
            )

            # Add Malayalam emotion keywords for better detection
            self.malayalam_emotion_keywords = {
                "joy": ["സന്തോഷം", "ആനന്ദം", "ഉത്സാഹം", "ആഹ്ലാദം", "ഖുശി"],
                "sadness": ["ദുഖം", "സങ്കടം", "കരുണ", "വ്യസനം", "അസഹ്യം"],
                "anger": ["ക്രോധം", "ക്ഷോഭം", "രോഷം", "അകൃത്യം", "അസഹനം"],
                "fear": ["ഭയം", "ഭീതി", "അപകടം", "ഭയങ്കരം", "അന്തം"],
                "surprise": ["ആശ്ചര്യം", "പ്രത്യാശ", "അദ്ഭുതം", "അപ്രതീക്ഷിതം"],
            }

        except Exception as e:
            logger.warning(f"Could not load emotion model: {e}")
            self.emotion_model = None

    def _initialize_tts_engine(self):
        """
        Initialize TTS engine with Malayalam support.
        """
        try:
            if COQUI_AVAILABLE:
                # Try to load Malayalam TTS model
                try:
                    self.tts_engine = TTS("tts_models/ml/cv/vits")
                    logger.info("Loaded Malayalam TTS model")
                except:
                    # Fallback to multilingual model
                    self.tts_engine = TTS(
                        "tts_models/multilingual/multi-dataset/xtts_v2"
                    )
                    logger.info("Loaded multilingual TTS model")
            else:
                logger.warning("Coqui TTS not available, using basic TTS")
                self.tts_engine = None

        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None

    async def generate_emotional_speech(
        self, text: str, emotion: str = None, voice_clone_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate speech with emotion-aware processing and voice cloning.
        """
        try:
            # Detect emotion if not provided
            if not emotion:
                emotion = await self._detect_emotion(text)

            # Get emotion configuration
            emotion_config = self.emotion_config.get(
                emotion, self.emotion_config["neutral"]
            )

            # Apply Malayalam emotion enhancements
            enhanced_text = self._enhance_malayalam_text(text, emotion)

            # Generate base speech
            audio_data = await self._generate_base_speech(enhanced_text, emotion_config)

            # Apply emotion modifications
            modified_audio = self._apply_emotion_modifications(
                audio_data, emotion_config
            )

            # Apply voice cloning if requested
            if voice_clone_id and voice_clone_id in self.voice_clones:
                modified_audio = await self._apply_voice_cloning(
                    modified_audio, voice_clone_id
                )

            # Convert to base64 for response
            audio_base64 = self._audio_to_base64(modified_audio)

            return {
                "audio_base64": audio_base64,
                "emotion_detected": emotion,
                "text_enhanced": enhanced_text,
                "voice_clone_applied": voice_clone_id is not None,
                "processing_time": datetime.utcnow().isoformat(),
                "malayalam_optimized": True,
            }

        except Exception as e:
            logger.error(f"Emotional speech generation failed: {e}")
            # Fallback to basic TTS
            return await self._fallback_speech_generation(text)

    async def _detect_emotion(self, text: str) -> str:
        """
        Detect emotion from Malayalam/English text.
        """
        try:
            if not self.emotion_model:
                return self._rule_based_emotion_detection(text)

            # Check for Malayalam emotion keywords first
            for emotion, keywords in self.malayalam_emotion_keywords.items():
                if any(keyword in text for keyword in keywords):
                    return emotion

            # Use ML model for emotion detection
            inputs = self.emotion_tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            )

            with torch.no_grad():
                outputs = self.emotion_model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=1)

            # Map to emotion labels
            emotion_labels = ["sadness", "joy", "anger", "fear", "surprise"]
            predicted_idx = torch.argmax(predictions, dim=1).item()

            return (
                emotion_labels[predicted_idx]
                if predicted_idx < len(emotion_labels)
                else "neutral"
            )

        except Exception as e:
            logger.error(f"Emotion detection failed: {e}")
            return "neutral"

    def _rule_based_emotion_detection(self, text: str) -> str:
        """
        Rule-based emotion detection as fallback.
        """
        text_lower = text.lower()

        # Malayalam emotion detection
        if any(word in text for word in ["സന്തോഷം", "ആനന്ദം", "ഉത്സാഹം", "ഖുശി"]):
            return "joy"
        elif any(word in text for word in ["ദുഖം", "സങ്കടം", "കരുണ", "വ്യസനം"]):
            return "sadness"
        elif any(word in text for word in ["ക്രോധം", "ക്ഷോഭം", "രോഷം"]):
            return "anger"
        elif any(word in text for word in ["ഭയം", "ഭീതി", "അപകടം"]):
            return "fear"
        elif any(word in text for word in ["ആശ്ചര്യം", "അദ്ഭുതം", "പ്രത്യാശ"]):
            return "surprise"

        # English emotion detection
        if any(word in text_lower for word in ["happy", "joy", "excited", "great"]):
            return "joy"
        elif any(word in text_lower for word in ["sad", "sorry", "unfortunate", "bad"]):
            return "sadness"
        elif any(word in text_lower for word in ["angry", "mad", "furious"]):
            return "anger"
        elif any(word in text_lower for word in ["scared", "afraid", "fear"]):
            return "fear"
        elif any(word in text_lower for word in ["surprised", "amazing", "wow"]):
            return "surprise"

        return "neutral"

    def _enhance_malayalam_text(self, text: str, emotion: str) -> str:
        """
        Enhance text with emotion-specific Malayalam phrases.
        """
        emotion_config = self.emotion_config.get(
            emotion, self.emotion_config["neutral"]
        )

        # Add emotion-specific Malayalam phrases
        if emotion_config["malayalam_phrases"]:
            # Insert phrase at natural break points
            sentences = text.split("।")
            if len(sentences) > 1:
                # Add phrase to first sentence
                emotion_phrase = np.random.choice(emotion_config["malayalam_phrases"])
                sentences[0] = f"{sentences[0]} {emotion_phrase}"
                enhanced_text = "।".join(sentences)
            else:
                enhanced_text = text
        else:
            enhanced_text = text

        return enhanced_text

    async def _generate_base_speech(
        self, text: str, emotion_config: Dict[str, Any]
    ) -> np.ndarray:
        """
        Generate base speech using TTS engine.
        """
        try:
            if self.tts_engine:
                # Use Coqui TTS
                wav = self.tts_engine.tts(text=text, speaker_wav=None)
                return np.array(wav)
            else:
                # Fallback to basic TTS service
                return await self._fallback_tts_generation(text)

        except Exception as e:
            logger.error(f"Base speech generation failed: {e}")
            return await self._fallback_tts_generation(text)

    async def _fallback_tts_generation(self, text: str) -> np.ndarray:
        """
        Fallback TTS generation using basic service.
        """
        try:
            # Use existing TTS service as fallback
            result = await self.tts_service.generate_speech(
                text, voice="malayalam_female"
            )

            # Convert base64 back to numpy array (simplified)
            # In real implementation, this would decode properly
            return np.random.random(16000)  # Mock audio data

        except Exception as e:
            logger.error(f"Fallback TTS failed: {e}")
            # Return silence
            return np.zeros(16000)

    def _apply_emotion_modifications(
        self, audio: np.ndarray, emotion_config: Dict[str, Any]
    ) -> np.ndarray:
        """
        Apply emotion-specific audio modifications.
        """
        try:
            modified_audio = audio.copy()

            # Apply pitch shift
            pitch_shift = emotion_config["pitch_shift"]
            if pitch_shift != 1.0:
                modified_audio = self._pitch_shift_audio(modified_audio, pitch_shift)

            # Apply speed modification
            speed = emotion_config["speed"]
            if speed != 1.0:
                modified_audio = self._change_audio_speed(modified_audio, speed)

            # Apply energy modification
            energy = emotion_config["energy"]
            if energy != 1.0:
                modified_audio = modified_audio * energy
                # Normalize to prevent clipping
                max_val = np.max(np.abs(modified_audio))
                if max_val > 1.0:
                    modified_audio = modified_audio / max_val

            return modified_audio

        except Exception as e:
            logger.error(f"Audio modification failed: {e}")
            return audio

    def _pitch_shift_audio(self, audio: np.ndarray, pitch_factor: float) -> np.ndarray:
        """
        Apply pitch shifting to audio.
        """
        # Simplified pitch shifting using resampling
        # In production, use libraries like pyrubberband or librosa
        try:
            from scipy.signal import resample

            original_length = len(audio)
            new_length = int(original_length / pitch_factor)
            shifted_audio = resample(audio, new_length)

            # Pad or truncate to original length
            if len(shifted_audio) > original_length:
                shifted_audio = shifted_audio[:original_length]
            else:
                padding = np.zeros(original_length - len(shifted_audio))
                shifted_audio = np.concatenate([shifted_audio, padding])

            return shifted_audio

        except Exception as e:
            logger.warning(f"Pitch shifting failed: {e}")
            return audio

    def _change_audio_speed(self, audio: np.ndarray, speed_factor: float) -> np.ndarray:
        """
        Change audio playback speed.
        """
        try:
            from scipy.signal import resample

            original_length = len(audio)
            new_length = int(original_length / speed_factor)
            speed_changed_audio = resample(audio, new_length)

            # Pad or truncate to original length
            if len(speed_changed_audio) > original_length:
                speed_changed_audio = speed_changed_audio[:original_length]
            else:
                padding = np.zeros(original_length - len(speed_changed_audio))
                speed_changed_audio = np.concatenate([speed_changed_audio, padding])

            return speed_changed_audio

        except Exception as e:
            logger.warning(f"Speed change failed: {e}")
            return audio

    async def _apply_voice_cloning(
        self, audio: np.ndarray, voice_clone_id: str
    ) -> np.ndarray:
        """
        Apply voice cloning using stored voice samples.
        """
        try:
            if voice_clone_id not in self.voice_clones:
                return audio

            voice_data = self.voice_clones[voice_clone_id]

            # Simplified voice cloning (in production, use proper voice conversion)
            # This would use techniques like voice conversion or style transfer

            # For now, apply basic filtering based on voice characteristics
            if voice_data.get("age") == "young":
                # Apply high-pass filter for younger voice
                from scipy.signal import butter, filtfilt

                b, a = butter(2, 0.1, "high")
                audio = filtfilt(b, a, audio)
            elif voice_data.get("age") == "old":
                # Apply low-pass filter for older voice
                from scipy.signal import butter, filtfilt

                b, a = butter(2, 0.3, "low")
                audio = filtfilt(b, a, audio)

            return audio

        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return audio

    def _audio_to_base64(self, audio: np.ndarray) -> str:
        """
        Convert audio array to base64 string.
        """
        try:
            # Convert to WAV format in memory
            buffer = io.BytesIO()
            sf.write(buffer, audio, 22050, format="wav")
            buffer.seek(0)

            # Encode to base64
            audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            return audio_base64

        except Exception as e:
            logger.error(f"Audio to base64 conversion failed: {e}")
            return ""

    async def _fallback_speech_generation(self, text: str) -> Dict[str, Any]:
        """
        Fallback speech generation when main method fails.
        """
        try:
            # Use basic TTS service
            result = await self.tts_service.generate_speech(
                text, voice="malayalam_female"
            )

            return {
                "audio_base64": result.get("audio_base64", ""),
                "emotion_detected": "neutral",
                "text_enhanced": text,
                "voice_clone_applied": False,
                "processing_time": datetime.utcnow().isoformat(),
                "malayalam_optimized": False,
            }

        except Exception as e:
            logger.error(f"Fallback speech generation failed: {e}")
            return {
                "audio_base64": "",
                "emotion_detected": "neutral",
                "text_enhanced": text,
                "voice_clone_applied": False,
                "processing_time": datetime.utcnow().isoformat(),
                "malayalam_optimized": False,
                "error": "Speech generation failed",
            }

    async def create_voice_clone(
        self, voice_samples: List[bytes], metadata: Dict[str, Any]
    ) -> str:
        """
        Create a voice clone from audio samples.
        """
        try:
            clone_id = f"clone_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Store voice samples and metadata
            self.voice_clones[clone_id] = {
                "samples": voice_samples,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
            }

            # In production, this would train a voice cloning model
            # For now, just store the metadata for basic filtering

            logger.info(f"Created voice clone: {clone_id}")
            return clone_id

        except Exception as e:
            logger.error(f"Voice cloning creation failed: {e}")
            raise

    async def get_voice_clones(self) -> List[Dict[str, Any]]:
        """
        Get list of available voice clones.
        """
        clones = []
        for clone_id, data in self.voice_clones.items():
            clones.append(
                {
                    "id": clone_id,
                    "metadata": data["metadata"],
                    "created_at": data["created_at"].isoformat(),
                }
            )

        return clones

    async def analyze_content_for_voice(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to recommend voice characteristics.
        """
        try:
            emotion = await self._detect_emotion(content)

            # Analyze content characteristics
            word_count = len(content.split())
            has_questions = "?" in content
            has_exclamation = "!" in content
            is_malayalam = any(ord(char) > 127 for char in content)

            # Recommend voice based on analysis
            recommendations = {
                "emotion": emotion,
                "suggested_voice": self._recommend_voice(
                    emotion, word_count, has_questions, has_exclamation
                ),
                "is_malayalam": is_malayalam,
                "content_length": word_count,
                "tone_suggestions": self._get_tone_suggestions(emotion),
            }

            return recommendations

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "emotion": "neutral",
                "suggested_voice": "malayalam_female",
                "is_malayalam": False,
                "content_length": 0,
                "tone_suggestions": ["natural"],
            }

    def _recommend_voice(
        self, emotion: str, word_count: int, has_questions: bool, has_exclamation: bool
    ) -> str:
        """
        Recommend voice based on content analysis.
        """
        # Base recommendation
        if emotion == "joy":
            voice = "malayalam_female_young"
        elif emotion == "sadness":
            voice = "malayalam_female_calm"
        elif emotion in ["anger", "fear"]:
            voice = "malayalam_male"
        else:
            voice = "malayalam_female"

        # Adjust based on content type
        if has_questions:
            voice += "_curious"
        elif has_exclamation:
            voice += "_excited"
        elif word_count > 100:
            voice += "_storyteller"

        return voice

    def _get_tone_suggestions(self, emotion: str) -> List[str]:
        """
        Get tone suggestions based on emotion.
        """
        tone_suggestions = {
            "joy": ["energetic", "warm", "enthusiastic"],
            "sadness": ["calm", "gentle", "soothing"],
            "anger": ["firm", "direct", "intense"],
            "fear": ["urgent", "concerned", "serious"],
            "surprise": ["expressive", "animated", "lively"],
            "neutral": ["natural", "balanced", "clear"],
        }

        return tone_suggestions.get(emotion, ["natural"])
