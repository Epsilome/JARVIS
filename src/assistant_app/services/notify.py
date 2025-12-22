try:
    from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
    from winrt.windows.data.xml.dom import XmlDocument
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False

def toast(title: str, msg: str):
    """Windows toast; falls back to stdout on non-Windows."""
    if WINRT_AVAILABLE:
        try:
            xml = XmlDocument()
            xml.load_xml(
                f"<toast><visual><binding template='ToastGeneric'>"
                f"<text>{title}</text><text>{msg}</text>"
                f"</binding></visual></toast>"
            )
            notifier = ToastNotificationManager.create_toast_notifier("Assistant")
            notifier.show(ToastNotification(xml))
        except Exception as e:
            print(f"[NOTIFY] Error: {e}")
    else:
        # Fallback
        print(f"[NOTIFY] {title}: {msg}")

