import pyttsx3
import logging

logger = logging.getLogger(__name__)

def speak(text: str):
    """
    Speaks the given text using the system's TTS engine.
    Initializes a new engine instance each time to avoid event loop issues.
    """
    try:
        engine = pyttsx3.init()
        
        # Try to set a better voice (usually index 1 is female/Zira on Windows)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
            
        # Set properties to ensure it's audible and clear
        engine.setProperty('rate', 170) 
        engine.setProperty('volume', 1.0)
        
        logger.info(f"Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        logger.error(f"Error during speech: {e}")
