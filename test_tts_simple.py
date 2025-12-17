import asyncio
import edge_tts

VOICE = "en-US-AriaNeural"
TEXT = "Hello world. This is a test."
OUTPUT = "test_audio.mp3"

async def main():
    print(f"Generating audio for: '{TEXT}'")
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT)
    print("Done.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
