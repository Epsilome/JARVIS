
import flet as ft
import random
import asyncio
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_WARNING, IRON_BG

class VoiceVisualizer(ft.Container):
    def __init__(self):
        super().__init__()
        self.bars = []
        self.is_active = False
        self.height = 100
        self.border_radius = 8
        self.border = ft.border.all(1, ft.Colors.with_opacity(0.3, IRON_CYAN))
        self.padding = 20
        from assistant_app.interfaces.gui.theme import BLACK_PIXEL_B64
        self.bgcolor = IRON_BG  # Use exact page background color
        
        # Create 30 bars
        self.row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4
        )
        
        for _ in range(30):
            bar = ft.Container(
                width=6,
                height=10,
                bgcolor=IRON_CYAN,
                border_radius=4,
                animate_size=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
            )
            self.bars.append(bar)
            self.row.controls.append(bar)
            
        self.content = self.row
        
        # Corner accents (decorative)
        self.stack = ft.Stack([
            self.row,
            # Top Left Corner
            ft.Container(width=10, height=10, top=0, left=0, border=ft.border.only(top=ft.border.BorderSide(2, IRON_CYAN), left=ft.border.BorderSide(2, IRON_CYAN))),
            # Bottom Right Corner
            ft.Container(width=10, height=10, bottom=0, right=0, border=ft.border.only(bottom=ft.border.BorderSide(2, IRON_CYAN), right=ft.border.BorderSide(2, IRON_CYAN))),
        ])
        
        self.content = self.stack

    def set_state(self, is_listening: bool):
        self.is_active = is_listening
        if not is_listening:
            # Reset bars
            for bar in self.bars:
                bar.height = 10
                bar.bgcolor = ft.Colors.with_opacity(0.3, IRON_CYAN)
            self.update()

    async def animate_loop(self):
        """Must be run as a task in the main loop"""
        while True:
            if self.is_active:
                for bar in self.bars:
                    # Randomize height to simulate waveform
                    height = random.randint(10, 60)
                    # Center bars (higher) vs edges (lower)
                    
                    bar.height = height
                    bar.bgcolor = IRON_CYAN
                self.update()
            await asyncio.sleep(0.1)
