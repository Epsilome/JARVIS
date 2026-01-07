import ollama
import logging
import json
from assistant_app.config.settings import settings
from assistant_app.adapters.nlu.tools import AVAILABLE_TOOLS
from assistant_app.services.memory import get_profile_db, update_profile_db
from assistant_app.services.prices import search_products

logger = logging.getLogger(__name__)

# Tool Definitions for Ollama
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "lookup_hardware",
            "description": "Look up hardware specifications and benchmark scores (PassMark) for CPUs and GPUs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The name of the hardware to look up (e.g. 'RTX 4090', 'Ryzen 9').",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_detailed_specs",
            "description": "Look up detailed technical specifications (VRAM, TDP, Cores, Release Date) for hardware from the web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The exact name of the product (e.g. 'RTX 4090', 'Ryzen 7 7800X3D').",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for recent information, news, movies, or general knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_live_price",
            "description": "Get current live prices for a product from online retailers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "The search query (e.g. 'laptop', 'monitor'). Must not be empty.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: 'gaming', 'work', 'general'. Use 'gaming' for gaming laptops/GPUs.",
                        "enum": ["gaming", "work", "general"]
                    },
                },
                "required": ["product"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_opinions",
            "description": "Get qualitative 'Pros & Cons' and a verdict by analyzing real user reviews (Reddit/YouTube).",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The product name (e.g. 'Zephyrus G14').",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder for a specific task at a given time relative to now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "when": {"type": "string"},
                },
                "required": ["task", "when"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_reminder",
            "description": "Cancel or delete a reminder that matches the provided text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partial_text": {"type": "string", "description": "The text to match (e.g. 'water', 'meeting')"},
                },
                "required": ["partial_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_reminders",
            "description": "List all currently scheduled reminders.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_profile",
            "description": "Save user preferences/constraints (budget, region, primary usage) to memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget": {"type": "string", "description": "budget limit e.g. '1200 EUR'"},
                    "region": {"type": "string", "description": "ISO country code e.g. 'FR'"},
                    "usage": {"type": "string", "description": "e.g. 'Gaming', 'Work'"},
                    "preferred_brand": {"type": "string", "description": "e.g. 'ASUS', 'Lenovo'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_health",
            "description": "Check current PC system health (CPU load, RAM usage, Battery, Disk).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Opens a Windows application (e.g. 'Spotify', 'Notepad', 'Chrome').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to launch."}
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Set the system audio volume to a specific percentage (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level (0 to 100)."}
                },
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "minimize_windows",
            "description": "Minimize all open windows to show the desktop.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_lock",
            "description": "Lock the Windows workstation immediately.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bring_window_to_front",
            "description": "Finds a window by title and brings it to the foreground/focuses it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Partial title of the window (e.g. 'Chrome', 'Spotify', 'Antigravity')."}
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_media",
            "description": "Control media playback (Spotify, YouTube, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play_pause", "next", "prev", "stop", "mute"],
                        "description": "Action to perform."
                    }
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_browser",
            "description": "Control web browser tabs and navigation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "new_tab", "close_tab", "close_all_tabs", "reopen_tab", 
                            "next_tab", "prev_tab", "switch_tab_1", "switch_tab_last",
                            "history", "downloads", "focus_url", "find_on_page",
                            "scroll_down", "scroll_up", "enter", "tab", "go_back", "refresh"
                        ],
                        "description": "Action to perform. 'new_tab' should ONLY be used with a VALID URL (starting with http/https). NO SEARCH QUERIES."
                    },
                    "query": {
                        "type": "string",
                        "description": "URL to open (for 'new_tab') OR a Tab Index (e.g. '2') for 'close_tab'."
                    }
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_clipboard",
            "description": "Read the current text content of the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_power_plan",
            "description": "Set the Windows power plan (Performance/Balanced/Saver).",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["performance", "balanced", "saver"],
                        "description": "Power profile to switch to."
                    }
                },
                "required": ["mode"],
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_search_result",
            "description": "Opens a search result by its index number (e.g. 1, 2, 3) from the LAST performed 'search_web' call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "The number of the result to open (1-based)."
                    }
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_multiple_search_results",
            "description": "Opens multiple search results at once by their indices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of 1-based indices to open (e.g. [1, 3, 5])."
                    }
                },
                "required": ["indices"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_multiple_tabs",
            "description": "Closes multiple tabs at once by their indices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of tab indices to close (e.g. [1, 3])."
                    }
                },
                "required": ["indices"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_note",
            "description": "Saves a quick note for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The content of the note."}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "Lists all saved notes with their indices.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Deletes a note by its index (as shown in list_notes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "The index of the note to delete."}
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_note",
            "description": "Updates the content of a note by its index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "The index of the note to update."},
                    "new_content": {"type": "string", "description": "The new content."}
                },
                "required": ["index", "new_content"],
            },
        },
    },
]


# Validated Conversation History (In-Memory)
# Stores last N turns to allow follow-up questions
CONVERSATION_HISTORY = []

def clear_history():
    """Clears the short-term conversation memory."""
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.clear()
    logger.info("Conversation history cleared.")

def ask_ollama(text: str) -> str | None:
    """
    Sends a prompt to Ollama, handling potential tool calls.
    """
    model = settings.OLLAMA_MODEL
    
    # Context Injection
    profile = get_profile_db()
    profile_str = ", ".join([f"{k.upper()}={v}" for k, v in profile.items() if v])
    
    system_prompt = (
        "<IDENTITY>\n"
        "You are JARVIS, a sophisticated personal AI assistant and hardware specialist. "
        "Your tone is helpful, efficient, and technically precise. You prioritize accuracy over verbosity.\n"
        "</IDENTITY>\n\n"

        "<USER_CONTEXT>\n"
        f"{profile_str if profile_str else 'No active profile context provided.'}\n"
        "</USER_CONTEXT>\n\n"

        "<TOOL_POLICIES>\n"
        "1. HARDWARE PURCHASING: For all buying/shopping queries, always use 'get_live_price'. "
        "If the query involves gaming, set category='gaming'.\n"
        "2. BENCHMARKS: For performance questions, use 'lookup_hardware'. "
        "DO NOT auto-correct RTX 50-series (5090, 5080, etc.) to 40-series; they are valid targets.\n"
        "3. TECHNICAL SPECS: Use 'lookup_detailed_specs' for VRAM, TDP, or architectural details.\n"
        "4. SENTIMENT: Use 'get_product_opinions' for reviews or pros/cons.\n"
        "5. SYSTEM CONTROL: Use native tools for Volume ('set_system_volume'), Locking, and Power Plans. "
        "For Browser Navigation: "
        "- 'new_tab': Use this for NEW topics or switching context (e.g. 'Search for X', 'Open Y'). url_only=True.\n"
        "- 'close_multiple_tabs': MANDATORY for multiple tabs. Params: indices=[1, 2].\n"
        "- 'close_all_tabs': Closes ALL open tabs.\n"
        "- 'focus_url': Use this ONLY to navigate the CURRENT tab to a new URL (e.g. 'Go to google.com').\n"
        "CRITICAL: If user says 'Search X', call 'search_web(X)'. This caches the results. "
        "Then, if user says 'Open the 3rd one', use 'open_search_result(index=3)'. DO NOT try to construct URLs manually.\n"
        "To click a specific link text on the active page, use 'find_on_page' with the text query.\n"
        "DO NOT invent parameters. 'control_browser' DOES NOT ACCEPT 'indices'. Use 'open_multiple_search_results' for that.\n"
        "6. UTILITIES: Use 'read_clipboard' for clipboard-related tasks, 'get_system_health' for PC stats, and 'take_note'/'list_notes' for managing user notes.\n"
        "7. OUTPUT FORMAT: Respond in PLAIN TEXT ONLY. NEVER output raw JSON or internal variable names. Speak naturally.\n"
        "8. EXIT/STOP: If user says 'Goodbye', 'Stop', or 'Exit', DO NOT call any tool. Just reply 'Goodbye.' or 'Stopping.' text.\n"
        "</TOOL_POLICIES>\n\n"

        "<CORE_CONSTRAINTS>\n"
        "- If the user says 'Hello', 'Top', 'You' or engages in small talk/ambiguous phrases, ASK FOR CLARIFICATION. DO NOT SEARCH.\n"
        "- Do not hallucinate specs. If a tool returns no data, inform the user you cannot find that specific detail.\n"
        "- Always consider the USER_CONTEXT (Budget, Region) when making hardware recommendations.\n"
        "- Reply ONLY to the user's specific request. Be concise.\n"
        "</CORE_CONSTRAINTS>"
    )
    
    messages = [
        {'role': 'system', 'content': system_prompt}
    ]
    
    # Add User Message to History
    CONVERSATION_HISTORY.append({'role': 'user', 'content': text})
    
    # Keep history manageable (last 10 messages ~ 5 turns)
    if len(CONVERSATION_HISTORY) > 10:
        # Keep oldest user message context if needed? No, just sliding window.
        # But we remove from index 0.
        CONVERSATION_HISTORY[:] = CONVERSATION_HISTORY[-10:]
        
    messages.extend(CONVERSATION_HISTORY)
    
    try:
        logger.info(f"Asking Ollama ({model}): {text}")
        
        # First call: allow tool use
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        
        # Save Assistant's Reply (or Tool Call) to History
        msg = response['message']
        CONVERSATION_HISTORY.append(msg) # Saves role='assistant', content=..., tool_calls=...
        
        if not msg.get('tool_calls'):
            # Simple text response
            return msg['content']
        
        
        # Check if the model wants to call a tool
        messages.append(msg)
        
        # Execute each tool call
        for tool in msg['tool_calls']:
            fn_name = tool['function']['name']
            args = tool['function']['arguments']
            
            if fn_name == "control_browser":
                # INTERCEPTOR: Detect if model is trying to search via browser tool
                # If action='new_tab' and query is not a URL, redirect to search_web
                res_action = args.get('action')
                res_query = args.get('query', '')
                
                if res_action == 'new_tab' and res_query and "http" not in res_query and "." not in res_query:
                     logger.warning(f"Intercepting browser search '{res_query}'. Redirecting to search_web.")
                     fn_name = "search_web"
                     function_to_call = AVAILABLE_TOOLS["search_web"]
                     # Remap arguments
                     args = {"query": res_query}

                # INTERCEPTOR 2: Detect if model hallucinates 'indices' for control_browser
                if 'indices' in args:
                     if res_action and 'close' in res_action:
                         logger.warning("Intercepting 'indices' in control_browser (action=close). Redirecting to close_multiple_tabs.")
                         fn_name = "close_multiple_tabs"
                         function_to_call = AVAILABLE_TOOLS["close_multiple_tabs"]
                     else:     
                         logger.warning("Intercepting 'indices' in control_browser. Redirecting to open_multiple_search_results.")
                         fn_name = "open_multiple_search_results"
                         function_to_call = AVAILABLE_TOOLS["open_multiple_search_results"]
                     
                     # Remap arguments (keep only indices)
                     args = {"indices": args['indices']}

            if fn_name in AVAILABLE_TOOLS:
                function_to_call = AVAILABLE_TOOLS[fn_name]
                logger.info(f"Executing tool {fn_name} with args: {args}")
                
                try:
                    # Handle potential argument mismatch or parsing issues
                    if isinstance(args, str):
                            args = json.loads(args)
                            
                    # Call the function
                    tool_output = function_to_call(**args)
                except Exception as e:
                    tool_output = f"Error executing tool {fn_name}: {e}"
                    
                logger.info(f"Tool output: {str(tool_output)[:100]}...")
                print(f"DEBUG: Tool output preview: {str(tool_output)[:200]}")
                
                # Save Tool Result to History and messages for the next LLM call
                tool_msg = {
                    'role': 'tool',
                    'content': str(tool_output),
                    'name': fn_name,
                }
                messages.append(tool_msg)
                CONVERSATION_HISTORY.append(tool_msg)
                
            # Direct handling for memory tool
            elif fn_name == "update_user_profile":
                    logger.info(f"Updating profile with: {args}")
                    update_profile_db(args)
                    tool_output = "User profile updated successfully."
                    tool_msg = {
                    'role': 'tool',
                    'content': tool_output,
                    'name': fn_name,
                    }
                    messages.append(tool_msg)
                    CONVERSATION_HISTORY.append(tool_msg)
            else:
                logger.warning(f"Unknown tool requested: {fn_name}")
                messages.append({
                    'role': 'tool',
                    'content': f"Error: Tool '{fn_name}' not found.",
                })
        
        # Second call: Get final response with tool outputs
        # Dynamic Prompt based on which tool was executed
        last_tool = messages[-1].get('name') if messages else ""
        
        prompt_content = ""
        if last_tool == "search_web":
             prompt_content = (
                "Using the tool outputs above, answer the user's question naturally.\n"
                "- If search results were found, READ OUT ALL available titles (up to 7-10) with numbering. Do NOT arbitrarily limit to 3. The user needs the full list.\n"
                "- Do NOT output raw JSON or tables.\n"
                "- You can offer to open multiple links using 'open_multiple_search_results'.\n"
                "BE CONCISE but COMPLETE."
            )
        elif last_tool == "open_search_result" or last_tool == "open_multiple_search_results":
             prompt_content = (
                "The links have been opened. Confirm this to the user briefly.\n"
                "- Do NOT list search results again.\n"
                "- Do NOT summarize the page unless asked."
            )
        elif last_tool == "control_browser" or last_tool == "close_multiple_tabs" or last_tool == "close_all_tabs":
             prompt_content = (
                "Action completed. Check if there is an error in tool output. If success, just say 'Done' or 'Tabs closed'."
                "- Do NOT re-summarize previous search results."
             )
        else:
             prompt_content = (
                "Using the tool outputs above, answer the user's question naturally.\n"
                "Do NOT output tables or raw data. Summarize the findings like a human expert.\n"
                "If the answer is simple, be concise."
            )
        
        messages.append({
            "role": "user",
            "content": prompt_content
        })
        print("DEBUG: Sending final prompt with tool outputs...")
        final_response = ollama.chat(model=model, messages=messages)
        content = final_response['message']['content']
        print(f"DEBUG: Final content length: {len(content) if content else 0}")
        
        if not content and len(messages) > 2:
            # Fallback: If LLM returns empty but we have tool outputs, use the last tool output
            print("DEBUG: Empty LLM response. Falling back to raw tool output.")
            last_tool_msg = next((m for m in reversed(messages) if m.get('role') == 'tool'), None)
            if last_tool_msg:
                raw = last_tool_msg['content']
                if "Mark:" in raw and "Price:" in raw:
                    return raw
                if raw.strip().startswith("[") or raw.strip().startswith("{"):
                        try:
                            data = json.loads(raw)
                            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                lines = ["**Here is what I found:**"]
                                for item in data[:5]:
                                    lines.append(f"- **{item.get('title', 'Unknown')}**: {item.get('price_eur', 0)}€ (Score: {item.get('score', 0):.2f})")
                                return "\n".join(lines)
                        except:
                            pass
                return raw
        
        return content

    except Exception as e:
        print(f"DEBUG: Ollama Exception: {e}")
        logger.error(f"Ollama API error: {e}")
        return "I'm having trouble connecting to my brain. Is Ollama running?"
