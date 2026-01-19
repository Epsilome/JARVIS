
import flet as ft
import asyncio
from assistant_app.interfaces.gui.theme import IRON_CYAN, IRON_BG, BG_GRADIENT, IRON_WARNING, IRON_CYAN_DIM
from assistant_app.interfaces.gui.components.nav_rail import NavRail
from assistant_app.interfaces.gui.components.chat_window import ChatWindow
from assistant_app.interfaces.gui.components.voice_visualizer import VoiceVisualizer
from assistant_app.interfaces.gui.components.status_widget import StatusWidget

# Import Voice Logic (mocked or real)
try:
    from assistant_app.services.voice_command import process_voice_command
except ImportError:
    process_voice_command = None

def main(page: ft.Page):
    # === Page Config (Modern) ===
    page.title = "JARVIS // PROTOCOL 7 (PATCHED)"
    
    # Theme: Transparent Surface Tint is key to removing Grey Overlay in M3
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            surface_tint=ft.Colors.TRANSPARENT,
            # background="#050505", # Removed to fix TypeError
            # surface="#050505",    # Removed to fix TypeError
        ),
        use_material3=True 
    )
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = IRON_BG
    page.title = "JARVIS // PROTOCOL 7 (PATCHED)"
    page.theme_mode = ft.ThemeMode.DARK
    
    # FORCE OVERRIDE: Disable Material 3 to remove surface tinting
    page.theme = ft.Theme(
        # color_scheme_seed=IRON_CYAN,
        use_material3=False,  # NUCLEAR OPTION: Disable M3
        color_scheme=ft.ColorScheme(
            primary=IRON_CYAN,
            surface="#000000",
            on_surface=IRON_CYAN,
            surface_tint=ft.Colors.TRANSPARENT,
        )
    )

    page.padding = 0
    
    # Modern Window Properties
    page.window.width = 1200
    page.window.height = 800
    # page.window.center() # FIXME: Coroutine warning in sync main
    
    # === Components ===
    # 1. Navigation Rail (Left)
    nav_rail = NavRail(on_change=lambda index: print(f"Nav: {index}"))
    
    # 2. Chat Window (Center Top)
    chat_window = ChatWindow()
    chat_window.add_message("user", "Initialize protocol 7.")
    chat_window.add_message("jarvis", "Protocol 7 initiated. Systems online.")
    
    # 3. Waveform Visualizer (Center Middle)
    visualizer = VoiceVisualizer()
    
    # 4. Status Widget (Bottom Right)
    status_widget = StatusWidget()
    
    # 5. Mic Button (Center Bottom)
    is_listening = False
    
    def toggle_mic(e):
        nonlocal is_listening
        is_listening = not is_listening
        
        # Update Visuals
        mic_btn_container.shadow = ft.BoxShadow(spread_radius=10, blur_radius=30, color=IRON_CYAN) if is_listening else None
        mic_btn_container.border = ft.border.all(2, IRON_CYAN if not is_listening else IRON_WARNING)
        mic_icon.color = IRON_CYAN if not is_listening else IRON_WARNING
        mic_label.value = "LISTENING" if is_listening else "IDLE"
        mic_label.color = IRON_WARNING if is_listening else IRON_CYAN
        
        # Update Visualizer
        visualizer.set_state(is_listening)
        
        page.update()

    mic_icon = ft.Icon("mic", size=40, color=IRON_CYAN)
    mic_label = ft.Text("IDLE", size=10, color=IRON_CYAN, weight=ft.FontWeight.BOLD)
    
    BLACK_PIXEL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    # Mic Button - EXACTLY like StatusWidget
    mic_btn_inner = ft.Container(
        content=ft.Column([
            mic_icon,
            mic_label
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        padding=10,
        border=ft.border.all(1, IRON_CYAN_DIM),
        border_radius=4,  # Same as StatusWidget (NOT 50!)
        bgcolor=IRON_BG,  # Use exact page background color
    )

    # No GestureDetector - just the Container directly
    mic_btn_container = mic_btn_inner

    # === Layout Assembly ===
    # Using Stack to allow "Floating" feeling over the background
    
    # Center Column (Chat + Visualizer + Mic)
    center_content = ft.Column(
        [
            ft.Container(height=20, bgcolor=ft.Colors.TRANSPARENT), # Margin Top
            # Chat Window Frame
            ft.Container(chat_window, height=350, bgcolor=ft.Colors.TRANSPARENT), 
            
            ft.Container(height=20, bgcolor=ft.Colors.TRANSPARENT),
            
            # Visualizer Frame
            ft.Container(visualizer, height=100, bgcolor=ft.Colors.TRANSPARENT),
            
            ft.Container(height=30, bgcolor=ft.Colors.TRANSPARENT),
            
            # Mic Button in Center
            ft.Row([mic_btn_container], alignment=ft.MainAxisAlignment.CENTER),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Main Grid
    layout = ft.Row(
        [
            nav_rail,
            ft.Container(width=40, bgcolor=ft.Colors.TRANSPARENT), # Spacer Nav-Center
            ft.Container(center_content, expand=True, bgcolor=ft.Colors.TRANSPARENT), # Main Content Area
            ft.Container(width=40, bgcolor=ft.Colors.TRANSPARENT), # Right Margin
        ],
        expand=True
    )
    
    # Status Widget Positioning (Absolute: Bottom Right)
    # We use a Stack for the whole page
    final_stack = ft.Stack(
        [
            # Layer 0: Background Gradient/Image
             ft.Container(
                gradient=BG_GRADIENT,
                expand=True,
            ),
             # Optional: Grid Overlay Image could go here
            
            # Layer 1: Main Layout
            ft.Container(layout, padding=20, bgcolor=ft.Colors.TRANSPARENT),
            
            # Layer 2: Floating Status Widget
            ft.Container(status_widget, bottom=20, right=20, bgcolor=ft.Colors.TRANSPARENT),
        ],
        expand=True
    )

    page.add(final_stack)
    
    # Start background tasks
    page.run_task(visualizer.animate_loop)
    page.run_task(status_widget.update_stats)

ft.app(main)
