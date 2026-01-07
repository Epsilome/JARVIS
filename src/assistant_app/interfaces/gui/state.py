
import threading
from enum import Enum
import time

class ListeningMode(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"

class UIState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.cpu_usage: float = 0.0
        self.ram_usage: float = 0.0
        self.listening_mode: ListeningMode = ListeningMode.IDLE
        self.neural_logs: list[str] = []
        self.messages: list[dict] = [] # List of {"role":..., "text":...}
        self._observers = [] # Callbacks
        
    def subscribe(self, callback):
        """Unused currently, relying on polling in UI loop"""
        self._observers.append(callback)

    def update_cpu(self, usage: float):
        self.cpu_usage = usage
        # self.notify() # UI parses this on tick

    def update_mode(self, mode: ListeningMode):
        self.listening_mode = mode
        self.add_log(f"MODE: {mode.value}")

    def add_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.neural_logs.append(f"[{timestamp}] {message}")
        if len(self.neural_logs) > 20: # Changed from 50 to 20
            self.neural_logs.pop(0)

    def add_message(self, role: str, text: str):
        self.messages.append({"role": role, "text": text})
        if len(self.messages) > 10: # Keep last 10 messages
            self.messages.pop(0)

state = UIState()
