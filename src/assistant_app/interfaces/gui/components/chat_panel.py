
import flet as ft
from assistant_app.interfaces.gui.theme import IronTheme, IRON_CYAN, PANEL_BG

class ChatPanel(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.list_view = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
            padding=5,
        )
        
        self.content = self.list_view

    def update_messages(self, messages: list[dict]):
        self.list_view.controls.clear()
        
        for msg in messages:
            role = msg["role"]
            text = msg["text"]
            
            is_user = role == "user"
            align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
            bg_color = ft.Colors.with_opacity(0.15, ft.Colors.WHITE) if is_user else ft.Colors.with_opacity(0.15, IRON_CYAN)
            text_color = ft.Colors.WHITE if is_user else IRON_CYAN
            
            bubble = ft.Container(
                content=ft.Markdown(
                    text,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    on_tap_link=lambda e: self.page.launch_url(e.data),
                    selectable=True,
                ),
                bgcolor=bg_color,
                border_radius=10,
                padding=10,
                border=ft.border.all(1, ft.Colors.with_opacity(0.3, text_color)),
            )
            
            row = ft.Row(
                [bubble],
                alignment=align,
            )
            self.list_view.controls.append(row)
        
        if self.page:
            self.list_view.update()
