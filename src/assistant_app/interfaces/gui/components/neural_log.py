
import flet as ft
from assistant_app.interfaces.gui.theme import IronTheme, IRON_CYAN

class NeuralLog(ft.Container):
    def __init__(self):
        super().__init__()
        self.logs = ft.ListView(
            expand=True, 
            spacing=2, 
            padding=5, 
            auto_scroll=True,
            divider_thickness=0
        )
        
        self.content = IronTheme.glass_container(
            content=ft.Column([
                ft.Text("NEURAL FEED", style=IronTheme.text_style_header),
                ft.Divider(color=IRON_CYAN, height=1),
                ft.Container(content=self.logs, expand=True)
            ]),
            padding=15
        )
        # We need to set expand explicitly if this container should expand
        self.expand = True

    def update_logs(self, log_list: list[str]):
        # Diff update or rebuild? 
        # Rebuilding list items is expensive. 
        # Better: Clear and add if length differs significantly, or just append new?
        # For simplicity in V1, we'll re-populate if the list object changed reference or simply clear/add.
        self.logs.controls.clear()
        for log in log_list:
            self.logs.controls.append(ft.Text(f"> {log}", style=IronTheme.text_style_dim))
        
        if self.page:
            self.update()
