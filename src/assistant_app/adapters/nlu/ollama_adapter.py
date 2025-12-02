import ollama
import logging
from assistant_app.config.settings import settings

logger = logging.getLogger(__name__)

def ask_ollama(text: str) -> str | None:
    """
    Sends a prompt to the local Ollama instance and returns the response text.
    """
    model = settings.OLLAMA_MODEL
    try:
        logger.info(f"Asking Ollama ({model}): {text}")
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': text,
            },
        ])
        return response['message']['content']
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return "I'm having trouble connecting to my local brain. Is Ollama running?"
