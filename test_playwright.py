from assistant_app.adapters.system_control import control_browser
from assistant_app.adapters.browser.playwright_manager import browser_manager
import time

print("Testing Playwright Integration...")

# Test 1: Open URL
print("1. Opening Google...")
control_browser("new_tab", "https://tavily.com")
time.sleep(2)

# Test 2: Get Content
print("2. Reading Page Content...")
content = browser_manager.get_page_content()
if "Tavily" in content or "Search" in content or len(content) > 0:
    print(f"✅ Success! Read {len(content)} chars.")
else:
    print("❌ Failed to read content.")

# Test 3: Scroll
print("3. Scrolling...")
control_browser("scroll_down")
time.sleep(1)

# Test 4: Open Search Result Simulation
print("4. Opening DuckDuckGo (Simulation)...")
control_browser("open_url", "https://duckduckgo.com")
time.sleep(2)
content = browser_manager.get_page_content()
if "DuckDuckGo" in content:
     print("✅ Success! Navigated.")
else:
     print("❌ Failed navigation.")

print("\nTests Complete. Browser will remain open for inspection.")
# browser_manager.close()
