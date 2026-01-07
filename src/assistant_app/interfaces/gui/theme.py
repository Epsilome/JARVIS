
import flet as ft

# === Iron Man Color Palette ===
IRON_CYAN = "#00D4FF"
IRON_CYAN_DIM = "#006080"
IRON_RED = "#FF3030"
IRON_RED_DIM = "#8B0000"
IRON_GOLD = "#FFD700"

DARK_BG = "#0A0A0A"
PANEL_BG = ft.Colors.with_opacity(0.08, IRON_CYAN)
PANEL_BORDER = ft.Colors.with_opacity(0.4, IRON_CYAN)

# === Glow Effects ===
CYAN_GLOW = ft.BoxShadow(
    spread_radius=2,
    blur_radius=15,
    color=ft.Colors.with_opacity(0.5, IRON_CYAN),
)

TEXT_GLOW = ft.BoxShadow(
    spread_radius=1,
    blur_radius=8,
    color=ft.Colors.with_opacity(0.7, IRON_CYAN),
)

# === Glassmorphism Container Factory ===
def glass_container(
    content: ft.Control,
    width: int = None,
    height: int = None,
    padding: int = 15,
    blur_amount: int = 10,
    expand: bool = False,
) -> ft.Container:
    return ft.Container(
        content=content,
        width=width,
        height=height,
        padding=padding,
        expand=expand,
        bgcolor=PANEL_BG,
        border=ft.border.all(1, PANEL_BORDER),
        border_radius=12,
        blur=ft.Blur(blur_amount, blur_amount, ft.BlurTileMode.MIRROR),
        shadow=CYAN_GLOW,
    )

# === Text Styles with Glow ===
class IronTheme:
    font_family = "Consolas"
    
    @staticmethod
    def header_text(text: str, size: int = 14) -> ft.Text:
        return ft.Text(
            text.upper(),
            size=size,
            weight=ft.FontWeight.BOLD,
            color=IRON_CYAN,
            font_family=IronTheme.font_family,
            # Note: Text shadow is applied via Container wrapper if needed
        )
    
    @staticmethod
    def body_text(text: str, size: int = 12, color=ft.Colors.WHITE) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            color=color,
            font_family=IronTheme.font_family,
        )
    
    @staticmethod    
    def dim_text(text: str, size: int = 11) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            color=ft.Colors.GREY_500,
            font_family=IronTheme.font_family,
        )
