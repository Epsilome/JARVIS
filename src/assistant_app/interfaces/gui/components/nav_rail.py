
import flet as ft
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_CYAN_DIM, IronTheme, BLACK_PIXEL_B64, IRON_BG

class NavRail(ft.Container):
    def __init__(self, on_change=None):
        super().__init__()
        self.on_change = on_change
        self.selected_index = 0
        self.bgcolor = "#FF050505"  # ARGB: Full opacity black
        
        # Define Navigation Items
        self.nav_items = [
            {"icon": "home", "label": "HOME"},
            {"icon": "memory", "label": "SYSTEMS"},
            {"icon": "chat_bubble_outline", "label": "COMM"},
            {"icon": "storage", "label": "DATA"},
            {"icon": "settings", "label": "SETTINGS"},
        ]
        
        self.width = 100
        self.padding = ft.padding.only(top=40, bottom=20)
        self.border = ft.border.only(right=ft.border.BorderSide(1, ft.Colors.with_opacity(0.2, IRON_CYAN)))
        self.content = self._build_rail()

    def _build_rail(self):
        controls = [
            ft.Container(height=20), # Spacer top
            # Logo / Header
            ft.Container(
                content=ft.Text("JARVIS", color=IRON_CYAN, size=16, weight=ft.FontWeight.BOLD, font_family="Consolas"),
                padding=ft.padding.only(bottom=40),
                alignment=ft.Alignment(0, 0)
            )
        ]
        
        for i, item in enumerate(self.nav_items):
            is_selected = i == self.selected_index
            color = IRON_CYAN if is_selected else ft.Colors.with_opacity(0.5, IRON_CYAN)
            
            # Icon Button with Label
            btn_inner = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(item["icon"], color=color, size=24),
                        ft.Text(item["label"], color=color, size=10, weight=ft.FontWeight.BOLD)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=10,
                border_radius=8,
                bgcolor=ft.Colors.BLACK if is_selected else ft.Colors.TRANSPARENT,
            )
            
            if is_selected:
                # Add a left glowing border indicator for selected item
                btn_inner.border = ft.border.only(left=ft.border.BorderSide(3, IRON_CYAN))
                
            btn = ft.GestureDetector(
                content=btn_inner,
                on_tap=lambda e, idx=i: self._on_item_click(idx)
            )
                
            controls.append(btn)
            controls.append(ft.Container(height=15)) # Spacer between items

        return ft.Column(controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _on_item_click(self, index):
        self.selected_index = index
        self.content = self._build_rail()
        self.update()
        if self.on_change:
            self.on_change(index)
