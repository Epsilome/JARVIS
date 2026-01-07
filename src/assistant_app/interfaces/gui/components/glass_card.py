
import flet as ft
from assistant_app.interfaces.gui.theme import (
    IronTheme, IRON_CYAN, PANEL_BG, PANEL_BORDER, CYAN_GLOW
)

class GlassCard(ft.Container):
    def __init__(
        self,
        title: str,
        content: ft.Control,
        icon: str = "info_outline",
        width: int = None,
        height: int = None,
        expand: bool = False,
    ):
        super().__init__()
        
        self.width = width
        self.height = height
        self.expand = expand
        self.border_radius = 12
        self.bgcolor = PANEL_BG
        self.border = ft.border.all(1, PANEL_BORDER)
        self.padding = 15
        self.blur = ft.Blur(10, 10, ft.BlurTileMode.MIRROR)
        self.shadow = CYAN_GLOW
        
        header = ft.Row(
            [
                ft.Icon(icon, color=IRON_CYAN, size=14),
                IronTheme.header_text(title, size=11),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon("open_in_full", color=ft.Colors.with_opacity(0.5, IRON_CYAN), size=12),
                    on_click=lambda e: print(f"Expand {title}"),  # Placeholder
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )
        
        self.content = ft.Column(
            [
                header,
                ft.Divider(color=PANEL_BORDER, height=1, thickness=1),
                content,
            ],
            spacing=10,
        )
