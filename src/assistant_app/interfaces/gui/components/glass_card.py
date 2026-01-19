import flet as ft
from assistant_app.interfaces.gui.theme import (
    IronTheme, IRON_CYAN, PANEL_BG, PANEL_BORDER, CYAN_GLOW
)

class GlassCard(ft.Stack):
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
        
        # Layer 1: The Background Image (Dark Glass)
        # This replaces Container.bgcolor/image_src to avoid theme overrides.
        self.bg_image = ft.Image(
            src=r"d:/JARVIS/src/assistant_app/assets/glass_bg.png",
            fit="cover",
            opacity=0.9,
            width=width,
            height=height,
        )
        
        # Layer 2: The Content Container (Border, Layout)
        self.main_container = ft.Container(
            border=ft.border.all(1, PANEL_BORDER),
            border_radius=12,
            padding=0,
            bgcolor=ft.Colors.TRANSPARENT, # FORCE TRANSPARENCY to reveal Image
            content=ft.Stack(
                controls=[
                    # Header
                    ft.Icon(icon, color=IRON_CYAN, size=14, top=8, left=5),
                    ft.Container(
                        content=IronTheme.header_text(title, size=11),
                        top=8, left=25, height=20,
                        bgcolor=ft.Colors.TRANSPARENT, # Safety transparency
                    ),
                    ft.Icon("open_in_full", color=ft.Colors.with_opacity(0.5, IRON_CYAN), size=12, top=8, right=5),
                    
                    # Divider
                    ft.Container(height=1, bgcolor=PANEL_BORDER, opacity=0.5, top=35, left=0, right=0),
                    
                    # Content
                    content,
                ],
                expand=True
            ),
        )
        
        # Position Content
        content.top = 45
        content.left = 10
        content.right = 10
        content.bottom = 10
        content.expand = True

        # Assemble the Stack
        self.controls = [
            self.bg_image,      # Bottom Layer
            self.main_container # Top Layer
        ]

