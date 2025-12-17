from assistant_app.adapters.nlu.ollama_adapter import ask_ollama
from assistant_app.adapters.nlu.tts_edge import speak
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

print("--- Testing LLM + Tool (DBGPU) + TTS ---")
question = "What are the specs of the RTX 3080?"
response = ask_ollama(question)
print(f"\nFinal Response:\n{response}")

if response:
    print("\n--- Testing TTS ---")
    speak(response)
else:
    print("Error: No response from LLM")
