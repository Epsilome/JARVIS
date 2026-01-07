
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

def control_browser(action: str):
    """
    Controls browser tabs.
    Action: 'new_tab', 'close_tab', 'reopen_tab', 'history', 'downloads'
    """
    if not pyautogui: return

    act = action.lower().replace(" ", "_")
    logger.info(f"Browser Control: {act}")
    
    if act == "new_tab":
        pyautogui.hotkey('ctrl', 't')
    elif act == "close_tab":
        pyautogui.hotkey('ctrl', 'w')
    elif act == "reopen_tab":
        pyautogui.hotkey('ctrl', 'shift', 't')
    elif act in ["history", "show_history"]:
        pyautogui.hotkey('ctrl', 'h')
    elif act in ["downloads", "show_downloads"]:
        pyautogui.hotkey('ctrl', 'j')
    elif act == "focus_url":
        pyautogui.hotkey('ctrl', 'l')

def read_clipboard() -> str:
    """Reads text from system clipboard."""
    if not pyperclip:
        return "Error: Pyperclip not installed."
    try:
        content = pyperclip.paste()
        return content if content else "Clipboard is empty."
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
        "gaming": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" # Alias to High Perf
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
