import speech_recognition as sr
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Initialize Whisper Model (Lazy loading or global)
# "base.en" is fast and decent. "small.en" is better. "medium.en" is very accurate.
# Let's start with "small.en" for a balance of speed and accuracy on GPU.
MODEL_SIZE = "small.en"
_model = None

def get_model():
    global _model
    if _model is None:
        logger.info(f"Loading Faster Whisper model ({MODEL_SIZE})...")
        from faster_whisper import WhisperModel
        
        # Default to CPU to avoid 'cudnn_ops64_9.dll' errors on Windows
        # GPU requires specific cuDNN v9 installation which is often missing.
        logger.info("Using CPU (INT8) for stability.")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model

class VoiceListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._setup()

    def _setup(self):
        with self.microphone as source:
            logger.info("Adjusting for ambient noise (one-time)...")
            # Increase base threshold to ignore background chatter (Discord, etc.)
            self.recognizer.energy_threshold = 1000  # Start higher (default is 300)
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 1.0 # Reduce from 2.0 to stop listening sooner
            
            # Calibrate briefly
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")

    def listen(self, timeout: int = 5, phrase_time_limit: int = 15) -> str | None:
        try:
            with self.microphone as source:
                logger.info("Listening...")
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                except sr.WaitTimeoutError:
                    return None
            
            # Save audio to temp file for Whisper
            return self._transcribe(audio)
        except Exception as e:
            logger.error(f"Listening error: {e}")
            return None

    def _transcribe(self, audio) -> str | None:
        tmp_path = None
        try:
            logger.info("Recognizing with Whisper...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_path = tmp_file.name
            
            model = get_model()
            segments, info = model.transcribe(tmp_path, beam_size=5)
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"Recognized: {text}")
                return text
            return None
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

# Legacy/Helper function for backward compatibility if needed, 
# but main.py should use the class.
_listener = None
def listen_and_recognize(timeout: int = 5, phrase_time_limit: int = 15) -> str | None:
    global _listener
    if _listener is None:
        _listener = VoiceListener()
    return _listener.listen(timeout, phrase_time_limit)
