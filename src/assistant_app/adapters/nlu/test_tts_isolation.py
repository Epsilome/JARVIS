
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTS_TEST")

def test_kokoro_cpu():
    print("\n--- Testing Kokoro TTS (CPU Mode) ---")
    
    import torch
    print(f"Original torch.cuda.is_available: {torch.cuda.is_available()}")
    
    # Simulate broken CUDA by monkeypatching
    torch.cuda.is_available = lambda: False
    print(f"Patched torch.cuda.is_available: {torch.cuda.is_available()}")

    try:
        from RealtimeTTS import TextToAudioStream, KokoroEngine
        print("2. Imports successful.")

        print("3. Initializing KokoroEngine (voice='af_bella') on CPU...")
        engine = KokoroEngine(voice="af_bella")
        print("   ✅ Engine initialized.")
        
        print("4. Creating Stream...")
        stream = TextToAudioStream(engine)
        print("   ✅ Stream created.")
        
        print("5. Speaking...")
        stream.feed("This is a test of the Kokoro voice on CPU.")
        stream.play()
        print("✅ Playback finished.")
        
    except Exception as e:
        print(f"\n❌ FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kokoro_cpu()
