"""
J.A.R.V.I.S. Dashboard - WORKING VERSION with GPU Stats
Last confirmed working at 12:01
"""
import flet as ft
import psutil
import datetime

# GPU Monitoring (NVIDIA)
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except Exception:
    GPU_AVAILABLE = False

# === Theme ===
IRON_CYAN = "#00D4FF"
IRON_RED = "#FF3030"
DARK_BG = "#050505"
PANEL_BG = ft.Colors.with_opacity(0.08, IRON_CYAN)
PANEL_BORDER = ft.Colors.with_opacity(0.4, IRON_CYAN)

# === Debug ===
DEBUG_MODE = False
DEBUG_BORDER = ft.border.all(2, ft.Colors.RED) if DEBUG_MODE else None

# === Glass Panel (with enhanced glow) ===
def glass_panel(title, content, width=None, expand=False):
    return ft.Container(
        content=ft.Column([
            ft.Text(title.upper(), color=IRON_CYAN, size=11, weight=ft.FontWeight.BOLD),
            ft.Divider(color=PANEL_BORDER, height=1),
            content,
        ], spacing=8),
        width=width,
        expand=expand,
        bgcolor=PANEL_BG,
        border=ft.border.all(1, PANEL_BORDER),
        border_radius=12,
        padding=15,
        shadow=ft.BoxShadow(
            spread_radius=4,
            blur_radius=25,
            color=ft.Colors.with_opacity(0.5, IRON_CYAN),
            offset=ft.Offset(0, 0),
        ),
    )

# === Arc Reactor with Animation Support ===
def create_reactor(size=180):
    ring_configs = [
        (1.0, 3, IRON_CYAN),
        (0.75, 2, ft.Colors.with_opacity(0.6, IRON_CYAN)),
        (0.50, 2, ft.Colors.with_opacity(0.8, IRON_CYAN)),
    ]
    rings = []
    
    # Outer ring with rotation animation
    outer_size = size * 1.0
    outer_offset = (size - outer_size) / 2
    outer_ring = ft.Container(
        width=outer_size,
        height=outer_size,
        border_radius=outer_size / 2,
        border=ft.border.all(3, IRON_CYAN),
        left=outer_offset,
        top=outer_offset,
        rotate=ft.Rotate(angle=0, alignment=ft.Alignment(0, 0)),
        animate_rotation=ft.Animation(300, ft.AnimationCurve.LINEAR),
    )
    rings.append(outer_ring)
    
    # Inner rings (static)
    for ratio, width, color in ring_configs[1:]:
        ring_size = size * ratio
        offset = (size - ring_size) / 2
        rings.append(ft.Container(
            width=ring_size,
            height=ring_size,
            border_radius=ring_size / 2,
            border=ft.border.all(width, color),
            left=offset,
            top=offset,
        ))
    
    # Glowing Core with scale animation
    core_size = size * 0.25
    core_offset = (size - core_size) / 2
    core = ft.Container(
        width=core_size,
        height=core_size,
        border_radius=core_size / 2,
        bgcolor=ft.Colors.with_opacity(0.8, IRON_CYAN),
        shadow=ft.BoxShadow(spread_radius=10, blur_radius=50, color=ft.Colors.with_opacity(0.95, IRON_CYAN)),
        left=core_offset,
        top=core_offset,
        animate_scale=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
        scale=ft.Scale(1.0),
    )
    rings.append(core)
    
    reactor_stack = ft.Stack(rings, width=size, height=size)
    return reactor_stack, outer_ring, core  # Return controls for animation

def main(page: ft.Page):
    page.title = "J.A.R.V.I.S. // System Interface"
    page.bgcolor = DARK_BG
    page.padding = 20
    page.window_width = 1200
    page.window_height = 750
    
    # === Dynamic Elements ===
    cpu_bar = ft.ProgressBar(value=0, color=IRON_CYAN, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), bar_height=6)
    cpu_text = ft.Text("0%", color=ft.Colors.GREY_400, size=11)
    ram_bar = ft.ProgressBar(value=0, color=IRON_CYAN, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), bar_height=6)
    ram_text = ft.Text("0 GB", color=ft.Colors.GREY_400, size=11)
    gpu_bar = ft.ProgressBar(value=0, color=IRON_CYAN, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), bar_height=6)
    gpu_text = ft.Text("N/A", color=ft.Colors.GREY_400, size=11)
    vram_bar = ft.ProgressBar(value=0, color=IRON_CYAN, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), bar_height=6)
    vram_text = ft.Text("N/A", color=ft.Colors.GREY_400, size=11)
    uptime_text = ft.Text("00:00:00", color=IRON_CYAN, size=14)
    status_text = ft.Text("IDLE", color=IRON_CYAN, size=18, weight=ft.FontWeight.BOLD)
    time_text = ft.Text("--:--:--", color=IRON_CYAN, size=16, weight=ft.FontWeight.BOLD)
    date_text = ft.Text("Loading...", color=ft.Colors.GREY_400, size=10)
    
    # === Panel Contents ===
    stats_content = ft.Column([
        ft.Row([ft.Text("CPU", color=ft.Colors.WHITE, size=11), ft.Container(expand=True), cpu_text]),
        cpu_bar,
        ft.Container(height=3),
        ft.Row([ft.Text("RAM", color=ft.Colors.WHITE, size=11), ft.Container(expand=True), ram_text]),
        ram_bar,
        ft.Container(height=3),
        ft.Row([ft.Text("GPU", color=ft.Colors.WHITE, size=11), ft.Container(expand=True), gpu_text]),
        gpu_bar,
        ft.Container(height=3),
        ft.Row([ft.Text("VRAM", color=ft.Colors.WHITE, size=11), ft.Container(expand=True), vram_text]),
        vram_bar,
    ], spacing=3)
    
    weather_content = ft.Column([
        ft.Row([
            ft.Text("☀️", size=28),  # Emoji instead of broken icon
            ft.Column([
                ft.Text("24°C", color=ft.Colors.WHITE, size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Casablanca", color=IRON_CYAN, size=10),
            ], spacing=0),
        ], spacing=10),
        ft.Row([
            ft.Text("Humidity: 65%", color=ft.Colors.GREY_400, size=10),
            ft.Text("Wind: 12 km/h", color=ft.Colors.GREY_400, size=10),
        ], spacing=15),
    ], spacing=8)
    
    uptime_content = ft.Column([
        ft.Text("SESSION TIME", color=ft.Colors.GREY_500, size=9),
        uptime_text,
        ft.Container(height=8),
        ft.Row([
            ft.Column([ft.Text("Commands", color=ft.Colors.GREY_500, size=9), ft.Text("0", color=IRON_CYAN, size=18, weight=ft.FontWeight.BOLD)], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(width=30),
            ft.Column([ft.Text("Errors", color=ft.Colors.GREY_500, size=9), ft.Text("0", color=ft.Colors.GREEN, size=18, weight=ft.FontWeight.BOLD)], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.CENTER),
    ], spacing=4)
    
    # Improved chat empty state
    chat_placeholder = ft.Column([
        ft.Container(expand=True),
        ft.Column([
            ft.Text("💬", size=32),
            ft.Text("Say 'Jarvis' to begin", color=IRON_CYAN, size=14),
            ft.Text("or use the microphone below", color=ft.Colors.GREY_500, size=10),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
        ft.Container(expand=True),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    # === Layout ===
    left_col = ft.Container(
        content=ft.Column([
            ft.Container(content=glass_panel("System Stats", stats_content), height=200),
            ft.Container(content=glass_panel("Weather", weather_content), height=140),
            ft.Container(content=glass_panel("Uptime", uptime_content), height=150),
        ], spacing=15),
        width=260,
        border=DEBUG_BORDER,
    )
    
    # Create reactor with animation controls
    reactor_stack, outer_ring, core = create_reactor(180)
    pulse_growing = True
    
    center_col = ft.Container(
        content=ft.Column([
            ft.Container(expand=True),
            reactor_stack,
            ft.Container(height=15),
            status_text,
            ft.Text("Listening for wake word...", color=ft.Colors.GREY_500, size=12),
            ft.Container(expand=True),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        border=DEBUG_BORDER,
    )
    
    right_col = ft.Container(
        content=glass_panel("Conversation", chat_placeholder, expand=True),
        width=280,
        border=DEBUG_BORDER,
    )
    
    body = ft.Row([left_col, center_col, right_col], expand=True, spacing=20)
    
    # === Simple Header (no ft.Padding, flat structure) ===
    header = ft.Row([
        ft.Text("⚡", size=18),
        ft.Text("J.A.R.V.I.S.", color=IRON_CYAN, size=16, weight=ft.FontWeight.BOLD),
        ft.Container(width=10),
        ft.Text("● ONLINE", color="#00FF00", size=9),
        ft.Container(expand=True),
        time_text,
        ft.Container(width=10),
        date_text,
    ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    page.add(ft.Column([header, ft.Divider(color=IRON_CYAN, height=1), body], expand=True, spacing=10))
    
    # === Background Updates ===
    start_time = datetime.datetime.now()
    
    async def update_loop():
        import asyncio
        while True:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            uptime = datetime.datetime.now() - start_time
            now = datetime.datetime.now()
            
            # Update time/date header
            time_text.value = now.strftime("%I:%M:%S %p")
            date_text.value = now.strftime("%b %d, %Y")
            
            cpu_bar.value = cpu / 100
            cpu_text.value = f"{cpu:.0f}%"
            cpu_bar.color = IRON_RED if cpu > 80 else IRON_CYAN
            
            ram_bar.value = mem.percent / 100
            ram_text.value = f"{mem.used / (1024**3):.1f} GB"
            
            if GPU_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_bar.value = util.gpu / 100
                    gpu_text.value = f"{util.gpu}%"
                    vram_bar.value = mem_info.used / mem_info.total
                    vram_text.value = f"{mem_info.used / (1024**3):.1f} GB"
                except Exception:
                    pass
            
            # Reactor status colors (based on CPU load)
            nonlocal pulse_growing
            if cpu > 80:
                # CRITICAL - Red
                core.bgcolor = ft.Colors.with_opacity(0.9, "#FF3030")
                core.shadow = ft.BoxShadow(spread_radius=12, blur_radius=60, color=ft.Colors.with_opacity(0.95, "#FF3030"))
                outer_ring.border = ft.border.all(3, "#FF3030")
            elif cpu > 50:
                # WARNING - Yellow/Amber
                core.bgcolor = ft.Colors.with_opacity(0.9, "#FFAA00")
                core.shadow = ft.BoxShadow(spread_radius=10, blur_radius=50, color=ft.Colors.with_opacity(0.9, "#FFAA00"))
                outer_ring.border = ft.border.all(3, "#FFAA00")
            else:
                # NORMAL - Cyan
                core.bgcolor = ft.Colors.with_opacity(0.8, IRON_CYAN)
                core.shadow = ft.BoxShadow(spread_radius=10, blur_radius=50, color=ft.Colors.with_opacity(0.95, IRON_CYAN))
                outer_ring.border = ft.border.all(3, IRON_CYAN)
            
            # Pulsing core (still works!)
            if pulse_growing:
                core.scale.scale = min(1.15, core.scale.scale + 0.03)
                if core.scale.scale >= 1.15:
                    pulse_growing = False
            else:
                core.scale.scale = max(0.9, core.scale.scale - 0.03)
                if core.scale.scale <= 0.9:
                    pulse_growing = True
            
            h, r = divmod(int(uptime.total_seconds()), 3600)
            m, s = divmod(r, 60)
            uptime_text.value = f"{h:02d}:{m:02d}:{s:02d}"
            
            page.update()
            await asyncio.sleep(0.5)
    
    page.run_task(update_loop)

ft.app(target=main)
