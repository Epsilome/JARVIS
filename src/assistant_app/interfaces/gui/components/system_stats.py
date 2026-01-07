
import flet as ft
from assistant_app.interfaces.gui.theme import IronTheme, IRON_CYAN, IRON_RED, PANEL_BORDER

class SystemStats(ft.Column):
    def __init__(self):
        super().__init__()
        self.spacing = 12
        
        # CPU Bar
        self.cpu_bar = ft.ProgressBar(
            value=0,
            color=IRON_CYAN,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            bar_height=8,
            border_radius=4,
        )
        self.cpu_text = IronTheme.dim_text("0%")
        
        # RAM Bar
        self.ram_bar = ft.ProgressBar(
            value=0,
            color=IRON_CYAN,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            bar_height=8,
            border_radius=4,
        )
        self.ram_text = IronTheme.dim_text("0 GB")
        
        self.controls = [
            ft.Column([
                ft.Row([
                    IronTheme.body_text("CPU Usage", size=11),
                    ft.Container(expand=True),
                    self.cpu_text,
                ]),
                self.cpu_bar,
            ], spacing=4),
            ft.Column([
                ft.Row([
                    IronTheme.body_text("RAM Usage", size=11),
                    ft.Container(expand=True),
                    self.ram_text,
                ]),
                self.ram_bar,
            ], spacing=4),
        ]

    def update_stats(self, cpu_percent: float, ram_percent: float, ram_used_gb: float):
        self.cpu_bar.value = cpu_percent / 100
        self.cpu_text.value = f"{cpu_percent:.0f}%"
        
        self.ram_bar.value = ram_percent / 100
        self.ram_text.value = f"{ram_used_gb:.1f} GB"
        
        # Red warning for high CPU
        if cpu_percent > 80:
            self.cpu_bar.color = IRON_RED
        else:
            self.cpu_bar.color = IRON_CYAN
