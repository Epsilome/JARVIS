def toast(title: str, msg: str):
    """Windows toast; falls back to stdout on non-Windows."""
    try:
        from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
        from winrt.windows.data.xml.dom import XmlDocument
        xml = XmlDocument()
        xml.load_xml(
            f"<toast><visual><binding template='ToastGeneric'>"
            f"<text>{title}</text><text>{msg}</text>"
            f"</binding></visual></toast>"
        )
        notifier = ToastNotificationManager.create_toast_notifier("Assistant")
        notifier.show(ToastNotification(xml))
    except Exception:
        print(f"[NOTIFY] {title}: {msg}")
