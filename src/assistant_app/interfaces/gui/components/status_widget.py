
import flet as ft
import psutil
import asyncio
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_CYAN_DIM, IronTheme, IRON_BG

class StatusWidget(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 10
        self.border = ft.border.all(1, IRON_CYAN_DIM)
        self.border_radius = 4
        self.bgcolor = IRON_BG  # Use exact page background color
        
        self.cpu_text = ft.Text("CPU: --%", color=IRON_CYAN, size=10, font_family="Consolas")
        self.mem_text = ft.Text("MEM: --%", color=IRON_CYAN, size=10, font_family="Consolas")
        self.net_text = ft.Text("NET: SECURE", color=IRON_CYAN, size=10, font_family="Consolas")
        self.temp_text = ft.Text("TEMP: 32°C", color=IRON_CYAN, size=10, font_family="Consolas")
        
        self.content = ft.Row(
            [
                self.cpu_text,
                self._divider(),
                self.mem_text,
                self._divider(),
                self.net_text, 
                self._divider(),
                self.temp_text
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
    def _divider(self):
        return ft.Text("|", color=IRON_CYAN_DIM, size=10)

    async def update_stats(self):
        while True:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            
            self.cpu_text.value = f"CPU: {cpu}%"
            self.mem_text.value = f"MEM: {mem}%"
            self.update()
            await asyncio.sleep(1)
