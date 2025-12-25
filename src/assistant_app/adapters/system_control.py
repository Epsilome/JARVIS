import platform
import time

try:
    import pyautogui
    # Safety: Fail-safe moves mouse to corner to abort
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

from loguru import logger

def set_volume(level: int):
    """
    Set master volume to specific percentage [0-100] using PyCaw.
    """
    if not PYCAW_AVAILABLE:
        logger.error("PyCaw not installed or not working.")
        return False
        
    if platform.system() != "Windows":
        logger.warning("Volume control currently only implemented for Windows.")
        return False

    try:
        # PyCaw setup (Simplified for v2+)
        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume
        
        # Scale 0-100 to scalar 0.0-1.0
        
        # Scale 0-100 to scalar 0.0-1.0
        # Note: SetMasterVolumeLevelScalar is linear perception
        scalar = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        logger.info(f"Volume set to {level}%")
        return True
    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        return False

def lock_screen():
    """Locks the workstation."""
    if not pyautogui:
        logger.error("PyAutoGUI not installed.")
        return

    logger.info("Locking screen...")
    if platform.system() == "Windows":
        pyautogui.hotkey('win', 'l')
    elif platform.system() == "Darwin":
        pyautogui.hotkey('ctrl', 'cmd', 'q')
    else:
        logger.warning("Lock screen not implemented for this OS.")

def minimize_all():
    """Minimize all windows (Show Desktop)."""
    if not pyautogui: return
    
    if platform.system() == "Windows":
        pyautogui.hotkey('win', 'd')

def open_app(app_name: str):
    """
    Opens an app by typing its name in the system search.
    """
    if not pyautogui:
        logger.error("PyAutoGUI not installed.")
        return

    logger.info(f"Opening app: {app_name}")
    pyautogui.press('win')
    time.sleep(0.3)
    pyautogui.write(app_name, interval=0.05)
    time.sleep(0.5)
    pyautogui.press('enter')
