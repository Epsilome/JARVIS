import struct
import pyaudio
import pvporcupine
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class WakeWordListener:
    def __init__(self, access_key: str | None = None, sensitivity: float = 0.5):
        self.access_key = access_key or os.getenv("PORCUPINE_ACCESS_KEY")
        if not self.access_key:
            logger.warning("No PORCUPINE_ACCESS_KEY found. Wake word will not work.")
            self.porcupine = None
            return

        try:
            # "jarvis" is a built-in keyword in Porcupine (free tier)
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=['jarvis'],
                sensitivities=[sensitivity]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            logger.info(f"Wake Word Engine (Porcupine) Initialized. Keyword: 'Jarvis'")
            
        except Exception as e:
            logger.error(f"Failed to init Porcupine: {e}")
            self.porcupine = None

    def listen(self):
        """
        Blocking loop that listens for the wake word.
        Returns True when 'Jarvis' is detected.
        """
        if not self.porcupine:
            logger.error("Wake word engine not initialized.")
            return False
            
        logger.info("Listening for 'Jarvis'...")
        try:
            while True:
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    logger.info("Wake word detected!")
                    return True
                    
        except KeyboardInterrupt:
            return False
        except Exception as e:
            logger.error(f"Wake word loop error: {e}")
            return False

    def release_mic(self):
        """Fully release the microphone (close stream and PyAudio) for other apps."""
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.close()
                self.audio_stream = None
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
        
        if hasattr(self, 'pa') and self.pa:
            try:
                self.pa.terminate()
                self.pa = None
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
        
        logger.info("Microphone released (PyAudio terminated)")

    def acquire_mic(self):
        """Re-initialize PyAudio and open stream."""
        if not self.porcupine:
            return
            
        try:
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            logger.info("Microphone acquired (PyAudio initialized)")
        except Exception as e:
            logger.error(f"Error acquiring mic: {e}")

    def close(self):
        if self.porcupine:
            self.porcupine.delete()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        if hasattr(self, 'pa') and self.pa:
            self.pa.terminate()
