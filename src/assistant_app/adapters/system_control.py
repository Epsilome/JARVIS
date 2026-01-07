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

try:
    import pyperclip
except ImportError:
    pyperclip = None

import subprocess
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
        # COM Initialization for Thread Safety
        try:
             import comtypes
             comtypes.CoInitialize()
        except: pass

        # PyCaw setup (Simplified for v2+)
        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume
        
        # Scale 0-100 to scalar 0.0-1.0
        # Note: SetMasterVolumeLevelScalar is linear perception
        val = float(level)
        scalar = max(0.0, min(1.0, val / 100.0))
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
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        except Exception as e:
            logger.error(f"Failed to lock via ctypes: {e}")
            pyautogui.hotkey('win', 'l') # Fallback
    elif platform.system() == "Darwin":
        pyautogui.hotkey('ctrl', 'cmd', 'q')
    else:
        logger.warning("Lock screen not implemented for this OS.")

def focus_window(title_query: str):
    """Brings a window matching the title to the foreground."""
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title_query)
        if windows:
            win = windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            logger.info(f"Focused window: {win.title}")
            return True
        else:
            logger.warning(f"No window found matching '{title_query}'")
            return False
    except Exception as e:
        logger.error(f"Failed to focus window: {e}")
        return False

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

def control_media(action: str):
    """
    Controls media playback. 
    Action: 'play_pause', 'next', 'prev', 'stop', 'mute'
    """
    if not pyautogui: return
    
    key_map = {
        "play_pause": "playpause",
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "prev": "prevtrack",
        "previous": "prevtrack",
        "stop": "stop",
        "mute": "volumemute"
    }
    
    key = key_map.get(action.lower().replace(" ", "_"))
    if key:
        logger.info(f"Media Control: {action} -> {key}")
        pyautogui.press(key)
    else:
        logger.warning(f"Unknown media action: {action}")

from assistant_app.adapters.browser.playwright_manager import browser_manager

def control_browser(action: str, query: str = None):
    """
    Controls browser using Playwright.
    Action: 'new_tab', 'close_tab', 'reopen_tab', 'history', 'downloads', 'focus_url'
            'scroll_down', 'scroll_up', 'enter', 'tab', 'go_back', 'refresh', 'close_all_tabs'
    """
    # Ensure browser is running
    browser_manager.initialize()

    act = action.lower().replace(" ", "_")
    logger.info(f"Browser Control (b): {act} arg={query}")
    
    if act == "new_tab" or act == "open_url" or act == "focus_url":
        if query:
            if "search_web" in query or "lookup_" in query:
                 logger.warning(f"Blocked hallucination: {query}")
                 return
            
            # Auto-correction for common voice typos (e.g. "youtubecom")
            corrected_text = query.strip()
            if " " not in corrected_text and "." not in corrected_text:
                if corrected_text.endswith("com"):
                    corrected_text = corrected_text[:-3] + ".com"
                elif corrected_text.endswith("org"):
                    corrected_text = corrected_text[:-3] + ".org"
                    
            if "." not in corrected_text and "localhost" not in corrected_text:
                 # Likely a search query that leaked into open_url
                 # Redirect to Google search instead of blocking
                 logger.info(f"Input '{query}' seems to be a search query. Redirecting to Google.")
                 browser_manager.open_url(f"https://www.google.com/search?q={query}")
                 return

            # Ensure scheme
            if not corrected_text.startswith("http"):
                corrected_text = "https://" + corrected_text

            # Use Playwright to navigate
            browser_manager.open_url(corrected_text)
        else:
            # Just ensure browser is open
            browser_manager.initialize()
            
    elif act == "scroll_down":
        browser_manager.scroll("down")
    elif act == "scroll_up":
        browser_manager.scroll("up")
    elif act == "go_back":
        browser_manager.go_back()
    elif act == "refresh":
        browser_manager.refresh()
    elif act == "close_tab":
        # Parse optional index from text/query (e.g. "2" or "the 2nd one")
        idx = None
        if query:
             import re
             # Extract first number found
             match = re.search(r'\d+', query)
             if match:
                  try: idx = int(match.group(0))
                  except: pass
        browser_manager.close_tab(index=idx)
    elif act == "close_all_tabs":
        browser_manager.close_all_tabs()
    else:
        logger.warning(f"Action '{act}' not fully implemented in Playwright adapter yet.")

def read_clipboard() -> str:
    """Reads text from system clipboard."""
    if not pyperclip:
        return "Error: Pyperclip not installed."
    try:
        content = pyperclip.paste()
        if not content or not content.strip():
             return "Clipboard is empty."
             
        # Log snippet for debug
        snippet = content[:50].replace('\n', ' ')
        logger.info(f"Clipboard read ({len(content)} chars): {snippet}...")
        return content
    except Exception as e:
        logger.error(f"Clipboard read failed: {e}")
        return f"Error reading clipboard: {e}"

def set_power_mode(mode: str) -> str:
    """
    Sets Windows Power Plan.
    Mode: 'performance', 'balanced', 'saver'
    """
    # Standard Windows GUIDs
    schemes = {
        "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        "gaming": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    }
    
    guid = schemes.get(mode.lower())
    if not guid:
        return f"Unknown power mode: {mode}. Use: performance, balanced, saver."
        
    try:
        subprocess.run(["powercfg", "/setactive", guid], check=True, shell=True)
        return f"Power mode set to {mode}."
    except Exception as e:
        logger.error(f"Powercfg failed: {e}")
        return f"Failed to set power mode: {e}"
