
"""
Minimal test to verify Flet glassmorphism and glow effects work.
Run: python -m assistant_app.interfaces.gui.ui_test
"""
import flet as ft

# Colors
IRON_CYAN = "#00D4FF"
DARK_BG = "#0A0A0A"

def main(page: ft.Page):
    page.title = "UI Test"
    page.bgcolor = DARK_BG
    page.padding = 40
    
    # Test 1: Simple colored container
    test1 = ft.Container(
        content=ft.Text("Test 1: Simple Container", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.with_opacity(0.2, IRON_CYAN),
        border=ft.border.all(1, IRON_CYAN),
        border_radius=10,
        padding=20,
        width=300,
    )
    
    # Test 2: Container with blur (glassmorphism)
    test2 = ft.Container(
        content=ft.Text("Test 2: Blur Container", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.with_opacity(0.1, IRON_CYAN),
        border=ft.border.all(1, IRON_CYAN),
        border_radius=10,
        padding=20,
        width=300,
        blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
    )
    
    # Test 3: Container with shadow (glow)
    test3 = ft.Container(
        content=ft.Text("Test 3: Shadow Glow", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.with_opacity(0.15, IRON_CYAN),
        border=ft.border.all(1, IRON_CYAN),
        border_radius=10,
        padding=20,
        width=300,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.5, IRON_CYAN),
        ),
    )
    
    # Test 4: Arc Reactor (simple circles)
    reactor = ft.Stack(
        [
            ft.Container(
                width=200, height=200,
                border_radius=100,
                border=ft.border.all(4, IRON_CYAN),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Container(
                width=150, height=150,
                border_radius=75,
                border=ft.border.all(2, ft.Colors.with_opacity(0.5, IRON_CYAN)),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Container(
                width=80, height=80,
                border_radius=40,
                bgcolor=ft.Colors.with_opacity(0.6, IRON_CYAN),
                shadow=ft.BoxShadow(
                    spread_radius=5,
                    blur_radius=30,
                    color=ft.Colors.with_opacity(0.8, IRON_CYAN),
                ),
                alignment=ft.Alignment(0, 0),
            ),
        ],
        width=200,
        height=200,
    )
    
    page.add(
        ft.Text("JARVIS UI Test - Glassmorphism Debug", size=20, color=IRON_CYAN),
        ft.Divider(color=IRON_CYAN),
        ft.Row([
            ft.Column([test1, test2, test3], spacing=20),
            ft.Container(content=reactor, alignment=ft.Alignment(0, 0), expand=True),
        ], spacing=40, expand=True),
    )

ft.app(target=main)
