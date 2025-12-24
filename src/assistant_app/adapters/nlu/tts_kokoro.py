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
            logger.info("Initializing Kokoro TTS Engine (Local)...")
            # default_lang_code='a' is usually American English in Kokoro default map
            # 'af_bella' is a high quality female voice included in Kokoro
            _ENGINE = KokoroEngine(voice="af_bella") 
            _STREAM = TextToAudioStream(_ENGINE)
            logger.info("Kokoro TTS Initialized.")
        except Exception as e:
            logger.error(f"Failed to init Kokoro: {e}")
            _STREAM = False
            
    return _STREAM if _STREAM else None

def speak(text: str):
    """Speaks the given text using local Kokoro engine."""
    
    # 1. Try Kokoro
    stream = _get_stream()
    if stream:
        try:
            # Clean Markdown implementation
            # Remove asterisks, hashes, and list dashes that might be read aloud
            import re
            # Remove **bold**, *italic*, ### Headers
            clean_text = re.sub(r'[\*#`]', '', text) 
            # Remove leading "- " for lists to improve flow, or keep them? 
            # Usually "- " read as "dash" is annoying. replacing with comma pause might be better.
            clean_text = re.sub(r'\n-\s+', '\n, ', clean_text)
            
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
