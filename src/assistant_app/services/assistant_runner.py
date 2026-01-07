
import asyncio
import time
import logging
import threading
import typer
from assistant_app.adapters.nlu.wake_word import WakeWordListener
from assistant_app.adapters.nlu.speech_recognition import listen_and_recognize
from assistant_app.services.voice_command import process_voice_command
from assistant_app.interfaces.gui.state import state, ListeningMode

logger = logging.getLogger(__name__)

def run_voice_loop(stop_event: threading.Event):
    """
    Runs the main Assistant Voice Loop (Wake Word -> Listen -> Command).
    Designed to run in a background thread for the GUI.
    """
    logger.info("Initializing Voice Loop...")
    state.add_log("Initializing Auditory Systems...")
    
    try:
        ww = WakeWordListener()
    except Exception as e:
        logger.error(f"Failed to init Wake Word: {e}")
        state.add_log(f"ERROR: Wake Word Init Failed: {e}")
        return

    if ww.porcupine:
        logger.info("Wake Word ENABLED.")
        state.add_log("Wake Word: ENABLED")
    else:
        logger.warning("Wake Word DISABLED.")
        state.add_log("Wake Word: DISABLED (Continuous)")

    state.update_mode(ListeningMode.IDLE)

    while not stop_event.is_set():
        try:
            # 1. Wait for Wake Word
            if ww.porcupine:
                # ww.listen() blocks until keyword hearing
                # We need to make it interruptible by checking stop_event if possible?
                # Porcupine's listen() might not yield frequently. 
                # For now, we rely on it breaking or us killing the thread (not ideal).
                # Better: loop short listens? ww.listen() usually listens for one frame? 
                # Checking implementation... usually it processes one frame. 
                # Assuming standard PV implementation wraps a loop.
                # If wrapped, we might block. But usually we write a loop around .process().
                # Let's assume standard behavior for now.
                
                if not ww.listen(): 
                    # If it returns False or internal break
                    if stop_event.is_set(): break
                    continue
                
                # WAKE WORD DETECTED
                logger.info("Wake Word Detected!")
                state.update_mode(ListeningMode.LISTENING)
                state.add_log("Wake Word Detected. Listening...")
                
                # Optional Beep
                try: 
                    import winsound
                    winsound.Beep(1000, 200) 
                except: pass

            # 2. Listen for Command
            # We are now in LISTENING mode
            text = listen_and_recognize()
            
            # 3. Process
            if text:
                state.update_mode(ListeningMode.THINKING)
                state.add_log(f"Processing: '{text}'")
                state.add_message("user", text) # <--- ADDED
                try:
                    process_voice_command(text)
                except (KeyboardInterrupt, SystemExit):
                    # Propagate these
                    raise
                except typer.Exit:
                    # Voice command requested exit
                    logger.info("Voice command requested exit.")
                    state.add_log("Shutdown Sequence Initiated...")
                    stop_event.set()
                    break
                except Exception as e:
                    logger.error(f"Command Error: {e}")
                    state.add_log(f"Command Error: {e}")
                
                state.update_mode(ListeningMode.IDLE)
            else:
                # No speech detected or timeout
                state.update_mode(ListeningMode.IDLE)
            
        except (KeyboardInterrupt, SystemExit):
            break
        except Exception as e:
            logger.error(f"Voice Loop Error: {e}")
            state.add_log(f"Error: {e}")
            time.sleep(1)
        
    ww.close()
    logger.info("Voice Loop Stopped.")
    state.add_log("Voice Loop Terminated.")
