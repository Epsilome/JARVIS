import google.generativeai as genai
import logging
from assistant_app.config.settings import settings

logger = logging.getLogger(__name__)

_model = None

def _get_model():
    global _model
    if _model is None:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. LLM features disabled.")
            return None
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            return None
    return _model

def ask_gemini(text: str) -> str | None:
    """
    Sends a prompt to Gemini and returns the response text.
    Returns None if API key is missing or error occurs.
    """
    model = _get_model()
    if not model:
        return None

    try:
        logger.info(f"Asking Gemini: {text}")
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "I'm having trouble connecting to my brain right now."
