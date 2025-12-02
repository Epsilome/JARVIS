import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

def listen_and_recognize(timeout: int = 5, phrase_time_limit: int = 5) -> str | None:
    """
    Listens to the microphone and returns the recognized text.
    Returns None if no speech is detected or if it's unintelligible.
    """
    recognizer = sr.Recognizer()
    
    # Adjust for ambient noise
    with sr.Microphone() as source:
        logger.info("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 1.2  # Allow longer pauses
        logger.info("Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10) # Increased limit
        except sr.WaitTimeoutError:
            logger.info("Listening timed out.")
            return None

    try:
        logger.info("Recognizing...")
        text = recognizer.recognize_google(audio)
        logger.info(f"Recognized: {text}")
        return text
    except sr.UnknownValueError:
        logger.info("Could not understand audio")
        return None
    except sr.RequestError as e:
        logger.error(f"Could not request results from Google Speech Recognition service; {e}")
        return None
