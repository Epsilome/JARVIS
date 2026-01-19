
import flet as ft

# === Iron Man / Techno Palette ===
# Primary Colors
IRON_CYAN = "#00E5FF"       # Main accent (Lines, Text, Glows)
IRON_CYAN_DIM = "#006080"   # Secondary accent
IRON_BG = "#050505"         # Deep Background
IRON_GLASS = "#0A0A0A"      # Panel Background (semi-transparent ideally, but using solid for contrast if needed)

# Secondary/Functional Colors
IRON_WARNING = "#FFC107"    # Amber/Gold for Processing/Warning
IRON_ERROR = "#FF3030"      # Red for Error/Critical
IRON_SUCCESS = "#00FF00"    # Green for Online/Success
IRON_WHITE = "#FFFFFF"

# Opacity Variants (ARGB) - Fixing "Grey" issue by using explicit Hex
IRON_CYAN_10 = "#1A00E5FF"
IRON_CYAN_05 = "#0D00E5FF"
IRON_BG_90 = "#E6050505"
IRON_BG_TRANSPARENT = "#00000000"
IRON_BLACK_20 = "#33000000"

# Gradients (LinearGradient objects)

BG_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
    colors=[
        "#000000",
        "#0A0A0A",
        "#050C10", # Slight Cyan tint at bottom right
    ],
)

# Hard override for stubborn backgrounds
BLACK_GRADIENT = ft.LinearGradient(
    colors=["#050505", "#050505"],
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
)

# 1x1 Black Pixel Base64 (Forcing Texture Rendering)
BLACK_PIXEL_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="


# === Text Styles ===
class IronTheme:
    font_family = "Consolas" # Monospace for terminal feel
    
    @staticmethod
    def header_text(text: str, size: int = 14, color: str = IRON_CYAN) -> ft.Text:
        return ft.Text(
            text.upper(),
            size=size,
            weight=ft.FontWeight.BOLD,
            color=color,
            font_family=IronTheme.font_family,
            spans=[ft.TextSpan(text, style=ft.TextStyle(shadow=ft.BoxShadow(blur_radius=10, color=color)))] if color == IRON_CYAN else []
        )
    
    @staticmethod
    def body_text(text: str, size: int = 12, color: str = IRON_WHITE) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            color=color,
            font_family=IronTheme.font_family,
        )

# === Effects ===
GLOW_CYAN = ft.BoxShadow(
    spread_radius=1,
    blur_radius=15,
    color="#6600E5FF", # ARGB for 40% Opacity Cyan
)
