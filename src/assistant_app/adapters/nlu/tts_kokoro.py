from RealtimeTTS import TextToAudioStream, SystemEngine, KokoroEngine
import logging
import os
import warnings

# Suppress annoying PyTorch/Kokoro warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")

# Aggressively silence phonemizer
logging.getLogger("phonemizer").setLevel(logging.CRITICAL)
logging.getLogger("phonemizer.backend.espeak.wrapper").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

# Ensure FFmpeg is in PATH (required for pydub/RealtimeTTS)
ffmpeg_path = r"C:\Users\anase\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + ffmpeg_path

# Global instances to avoid reloading model
_stream = None
_engine = None

def _get_stream():
    global _stream, _engine
    if _stream is None:
        try:
            logger.info("Initializing Kokoro TTS Engine (RealtimeTTS)...")
            # voice='af_heart' is a good default for Kokoro
            # Note: speed is likely a property or set via method, or default is 1.0
            _engine = KokoroEngine(voice="af_heart")
            # _engine.speed = 1.0 # Set properly if supported
            _stream = TextToAudioStream(_engine)
        except Exception as e:
            logger.error(f"Failed to init Kokoro: {e}")
            raise e
    return _stream

def speak(text: str):
    """
    Speaks text using Kokoro (RealtimeTTS). 
    Falls back to SystemEngine (pyttsx3) if Kokoro fails.
    """
    try:
        stream = _get_stream()
        logger.info(f"Speaking (Kokoro): {text}")
        stream.feed(text)
        stream.play()
    except Exception as e:
        logger.error(f"Kokoro TTS failed: {e}. Switching to System Fallback.")
        _speak_system_fallback(text)

def _speak_system_fallback(text: str):
    try:
        # Create a fresh system engine for fallback
        engine = SystemEngine()
        stream = TextToAudioStream(engine)
        stream.feed(text)
        stream.play()
    except Exception as e:
        logger.error(f"System Fallback TTS failed: {e}")
