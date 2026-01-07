
import flet as ft
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_CYAN_DIM, IRON_RED, CYAN_GLOW

class ArcReactor(ft.Stack):
    """
    Iron Man's Arc Reactor - multiple spinning concentric rings.
    """
    def __init__(self, size: int = 300):
        super().__init__()
        self.size = size
        self.width = size
        self.height = size
        
        # Ring sizes (outer to inner)
        ring_configs = [
            {"radius": size * 0.48, "width": 4, "color": IRON_CYAN, "speed": 3},
            {"radius": size * 0.40, "width": 2, "color": ft.Colors.with_opacity(0.5, IRON_CYAN), "speed": -5},
            {"radius": size * 0.32, "width": 3, "color": IRON_CYAN, "speed": 4},
        ]
        
        self.rings = []
        for cfg in ring_configs:
            ring = ft.Container(
                width=cfg["radius"] * 2,
                height=cfg["radius"] * 2,
                border_radius=cfg["radius"],
                border=ft.border.all(cfg["width"], cfg["color"]),
                alignment=ft.Alignment(0, 0),
                # Enable rotation animation
                rotate=ft.Rotate(0, alignment=ft.Alignment(0, 0)),
                animate_rotation=ft.Animation(cfg["speed"] * 1000, ft.AnimationCurve.LINEAR),
            )
            self.rings.append(ring)
        
        # Core (glowing center)
        core_size = size * 0.25
        self.core = ft.Container(
            width=core_size,
            height=core_size,
            border_radius=core_size / 2,
            bgcolor=IRON_CYAN_DIM,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.8, IRON_CYAN),
            ),
        )
        
        # Assemble stack (center-aligned)
        self.controls = [
            ft.Container(content=ring, alignment=ft.Alignment(0, 0), expand=True)
            for ring in self.rings
        ] + [
            ft.Container(content=self.core, alignment=ft.Alignment(0, 0), expand=True)
        ]
        
    def did_mount(self):
        # Start spinning animation
        self._spin()
    
    def _spin(self):
        import math
        for i, ring in enumerate(self.rings):
            # Set target rotation (will animate due to animate_rotation)
            ring.rotate.angle = math.pi * 2 * (1 if i % 2 == 0 else -1)
            ring.update()
    
    def update_state(self, cpu_usage: float, mode=None):
        """Update reactor appearance based on system state."""
        color = IRON_CYAN
        
        if mode:
            from assistant_app.interfaces.gui.state import ListeningMode
            if mode == ListeningMode.LISTENING:
                color = "#00FF00"  # Green
            elif mode == ListeningMode.THINKING:
                color = "#FF00FF"  # Magenta
            elif mode == ListeningMode.SPEAKING:
                color = "#FFFFFF"  # White
        
        if cpu_usage > 80:
            color = IRON_RED
        
        # Update core glow
        self.core.shadow = ft.BoxShadow(
            spread_radius=5 + int(cpu_usage / 20),
            blur_radius=30 + int(cpu_usage / 5),
            color=ft.Colors.with_opacity(0.8, color),
        )
        self.core.bgcolor = ft.Colors.with_opacity(0.5, color)
        
        # Update ring colors
        for ring in self.rings:
            ring.border = ft.border.all(ring.border.top.width, color)
        
        if self.page:
            self.update()
