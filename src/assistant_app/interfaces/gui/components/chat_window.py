
import flet as ft
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_CYAN_DIM, IRON_BG, IronTheme

class ChatWindow(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.border_radius = 4
        from assistant_app.interfaces.gui.theme import BLACK_PIXEL_B64
        self.bgcolor = "#FF050505"  # ARGB: Full opacity black
        self.border = ft.border.all(1, IRON_CYAN_DIM)
        
        # Messages List that scrolls
        self.messages_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            expand=True,
            auto_scroll=True,
        )
        
        # Frame Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("CHAT", color=IRON_CYAN, size=12, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Icon("minimize", color=IRON_CYAN, size=14),
                    ft.Icon("close", color=IRON_CYAN, size=14),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border=ft.border.only(bottom=ft.border.BorderSide(1, IRON_CYAN_DIM))
        )
        
        # Corner decorations (Frame accents)
        self.content = ft.Stack([
            # Main content area
            ft.Column([
                header,
                ft.Container(content=self.messages_column, padding=10, expand=True)
            ], spacing=0, expand=True),
            
            # Decor: Top Left Corner Frame
            ft.Container(
                width=20, height=20, top=-1, left=-1,
                border=ft.border.only(
                    top=ft.border.BorderSide(2, IRON_CYAN),
                    left=ft.border.BorderSide(2, IRON_CYAN)
                )
            ),
             # Decor: Bottom Right Corner Frame
            ft.Container(
                width=20, height=20, bottom=-1, right=-1,
                border=ft.border.only(
                    bottom=ft.border.BorderSide(2, IRON_CYAN),
                    right=ft.border.BorderSide(2, IRON_CYAN)
                )
            ),
        ])
    
    def add_message(self, role: str, text: str):
        is_user = role.lower() == "user"
        
        # Bubble Style
        bubble_color = ft.Colors.with_opacity(0.1, IRON_CYAN) if is_user else ft.Colors.with_opacity(0.1, "#FFC107") # Cyan vs Amber
        border_color = IRON_CYAN if is_user else "#FFC107"
        align = ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START
        
        # Message Bubble
        bubble = ft.Container(
            content=ft.Column([
                ft.Text(role.upper(), color=border_color, size=10, weight=ft.FontWeight.BOLD),
                ft.Text(text, color=ft.Colors.WHITE, size=12, font_family="Consolas"),
            ], spacing=2),
            bgcolor=bubble_color,
            border=ft.border.only(
                left=ft.border.BorderSide(2, border_color) if not is_user else ft.border.BorderSide(0, ft.Colors.TRANSPARENT),
                right=ft.border.BorderSide(2, border_color) if is_user else ft.border.BorderSide(0, ft.Colors.TRANSPARENT),
            ),
            padding=10,
            border_radius=4,
            width=400, # Max width
        )
        
        row = ft.Row(
            [bubble],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        )
        
        self.messages_column.controls.append(row)
        try:
             if self.page:
                self.update()
        except Exception:
            pass
