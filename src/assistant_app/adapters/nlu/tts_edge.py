import asyncio
import edge_tts
import pygame
import tempfile
import os
import time
import logging

logger = logging.getLogger(__name__)

# Default voice: en-US-AriaNeural (Female, realistic)
VOICE = "en-US-AriaNeural"

async def _generate_audio(text: str, output_file: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def speak(text: str):
    """
    Speaks the given text using Edge TTS (online) and plays it with pygame.
    """
    try:
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name

        # Generate audio (async)
        # Sanitize text: remove newlines and excessive whitespace for TTS stability
        clean_text = " ".join(text.split())
        if not clean_text:
            logger.warning("TTS received empty text, skipping.")
            return

        try:
            asyncio.run(_generate_audio(clean_text, temp_filename))
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            logger.info("Falling back to offline TTS (pyttsx3)...")
            _speak_offline(text)
            return

        # Play audio using pygame
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(temp_filename)
            logger.info(f"Speaking (Edge TTS): {text}")
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Unload to release the file lock
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
        finally:
            # Clean up temporary file with retry
            for _ in range(3):
                try:
                    os.remove(temp_filename)
                    break
                except Exception:
                    time.sleep(0.5)
            else:
                logger.warning(f"Could not remove temp file {temp_filename} after retries.")

    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        logger.info("Falling back to offline TTS (pyttsx3)...")
        _speak_offline(text)

def _speak_offline(text: str):
    """Fallback using pyttsx3 (offline)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        logger.error(f"Offline TTS error: {e}")
