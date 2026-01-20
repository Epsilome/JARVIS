import logging
try:
    from RealtimeTTS import TextToAudioStream, KokoroEngine
    REALTIMETTS_AVAILABLE = True
except ImportError:
    REALTIMETTS_AVAILABLE = False

logger = logging.getLogger(__name__)

_STREAM = None
_ENGINE = None

def _get_stream():
    """Singleton to initialize the heavy Kokoro engine once."""
    global _STREAM, _ENGINE
    if not REALTIMETTS_AVAILABLE:
        return None
        
    if _STREAM is None:
        try:
            import os
            voice = os.getenv("TTS_VOICE", "af_bella")
            logger.info(f"Initializing Kokoro TTS Engine (Local) - CPU Forced (Eco Mode) - Voice: {voice}...")
            # Force CPU usage by hiding CUDA from Torch (Kokoro uses torch internally)
            import torch
            torch.cuda.is_available = lambda: False
            
            _ENGINE = KokoroEngine(voice=voice) 
            _STREAM = TextToAudioStream(_ENGINE)
            logger.info("Kokoro TTS Initialized.")
        except Exception as e:
            logger.error(f"Failed to init Kokoro: {e}")
            _STREAM = False
            
    return _STREAM if _STREAM else None

def preload_model():
    """Warm up the TTS engine to avoid latency on first speech."""
    try:
        if REALTIMETTS_AVAILABLE:
            _get_stream()
            logger.info("Kokoro TTS preloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to preload Kokoro: {e}")

def reload_voice(new_voice: str = None):
    """Reload TTS engine with a new voice. Allows hot-swapping voice without restart."""
    global _STREAM, _ENGINE
    
    if not REALTIMETTS_AVAILABLE:
        return False
    
    try:
        import os
        voice = new_voice or os.getenv("TTS_VOICE", "af_bella")
        logger.info(f"Reloading Kokoro TTS Engine with voice: {voice}...")
        
        # Clean up existing engine
        if _STREAM:
            try:
                _STREAM.stop()
            except:
                pass
        _STREAM = None
        _ENGINE = None
        
        # Force CPU usage
        import torch
        torch.cuda.is_available = lambda: False
        
        # Reinitialize with new voice
        _ENGINE = KokoroEngine(voice=voice)
        _STREAM = TextToAudioStream(_ENGINE)
        logger.info(f"Kokoro TTS reloaded with voice: {voice}")
        return True
    except Exception as e:
        logger.error(f"Failed to reload Kokoro: {e}")
        _STREAM = False
        return False

def speak(text: str):
    """Speaks the given text using local Kokoro engine."""
    
    # 1. Try Kokoro
    stream = _get_stream()
    if stream:
        try:
            # Clean Markdown and URLs for natural speech
            import re
            
            # Remove URLs (http://, https://, www.)
            clean_text = re.sub(r'https?://[^\s\]]+', '', text)
            clean_text = re.sub(r'www\.[^\s\]]+', '', clean_text)
            
            # Remove markdown links [text](url) - keep just the text
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)
            
            # Remove **bold**, *italic*, ### Headers, backticks
            clean_text = re.sub(r'[\*#`]', '', clean_text)
            
            # Remove leading "- " for lists (reads as "dash")
            clean_text = re.sub(r'\n-\s+', '\n, ', clean_text)
            
            # Remove bullet points (•)
            clean_text = clean_text.replace('•', ',')
            
            # Collapse whitespace
            clean_text = " ".join(clean_text.split())
            if not clean_text: return
            
            logger.info(f"Speaking (Kokoro): {clean_text[:50]}...")
            stream.feed(clean_text)
            stream.play() # Blocking playback
            return
        except KeyboardInterrupt:
            logger.info("Speech interrupted by user.")
            stream.stop()
            # Re-raise to ensure the main loop knows to stop if needed, 
            # or swallow if we just want to stop talking but keep app running?
            # User said "stop the assistant when he is talking", usually implies stopping that response.
            return
        except Exception as e:
            logger.error(f"Kokoro Error: {e}")
            
    # 2. Fallback to offline pyttsx3 if Kokoro fails
    logger.warning("Falling back to standard offline TTS...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"Fallback TTS failed: {e}")
