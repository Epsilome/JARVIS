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
        asyncio.run(_generate_audio(text, temp_filename))

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
            # Clean up temporary file
            try:
                os.remove(temp_filename)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_filename}: {e}")

    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        # Fallback to pyttsx3 could be added here if needed
