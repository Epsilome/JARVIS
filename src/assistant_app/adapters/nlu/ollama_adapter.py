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
]

def ask_ollama(text: str) -> str | None:
    """
    Sends a prompt to Ollama, handling potential tool calls.
    """
    model = settings.OLLAMA_MODEL
    
    # Context Injection
    profile = get_profile_db()
    profile_str = ", ".join([f"{k.upper()}={v}" for k, v in profile.items() if v])
    
    system_prompt = (
        "You are JARVIS, a helpful assistant and hardware expert. "
        "You have access to tools for looking up hardware benchmarks (PassMark), detailed specs (VRAM, TDP), live prices, and user opinions. "
        f"{'active USER CONTEXT: [' + profile_str + ']' if profile_str else ''}\n"
        "IMPORTANT RULES:\n"
        "1. For BUYING/PRICES/SHOPPING ('What can I afford?', 'Find cheap laptop'), use 'get_live_price'. Set category='gaming' for gaming PCs.\n"
        "2. For PERFORMANCE/BENCHMARKS ('Is 4090 fast?', 'Score for Ryzen 9'), use 'lookup_hardware'.\n"
        "3. For DETAILED SPECS (VRAM, Cores, TDP), use 'lookup_detailed_specs'.\n"
        "4. For OPINIONS/REVIEWS ('Is X good?', 'Pros/Cons'), use 'get_product_opinions'.\n"
        "5. For REMINDERS ('Remind me to X in Y'), use 'set_reminder'.\n"
        "6. For PREFERENCES ('My budget is X'), use 'update_user_profile'.\n"
        "7. For general chat/greetings ('Hello', 'Hi', 'Who are you?'), do NOT use any tools. Just reply text.\n"
        "8. Do not guess. Use the tools ONLY when necessary."
    )
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': text}
    ]
    
    try:
        logger.info(f"Asking Ollama ({model}): {text}")
        
        # First call: allow tool use
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            options={'temperature': 0.1}
        )
        
        message = response['message']
        
        # Check if the model wants to call a tool
        if message.get('tool_calls'):
            logger.info(f"Ollama requested tool calls: {len(message['tool_calls'])}")
            
            # Add the model's response (with tool calls) to history
            messages.append(message)
            
            # Execute each tool call
            for tool in message['tool_calls']:
                fn_name = tool['function']['name']
                args = tool['function']['arguments']
                
                if fn_name in AVAILABLE_TOOLS:
                    function_to_call = AVAILABLE_TOOLS[fn_name]
                    logger.info(f"Executing tool {fn_name} with args: {args}")
                    
                    try:
                        # Handle potential argument mismatch or parsing issues
                        # args is usually a dict
                        if isinstance(args, str):
                             args = json.loads(args)
                             
                        # Call the function
                        # Note: Our tools take simple args, but args dict keys match parameter names
                        # lookup_hardware(query=...)
                        tool_output = function_to_call(**args)
                    except Exception as e:
                        tool_output = f"Error executing tool {fn_name}: {e}"
                        
                    logger.info(f"Tool output: {tool_output[:100]}...")
                    print(f"DEBUG: Tool output preview: {str(tool_output)[:200]}")
                    
                    # Add tool result to messages
                    messages.append({
                        'role': 'tool',
                        'content': str(tool_output),
                    })
                    
                # Direct handling for memory tool
                elif fn_name == "update_user_profile":
                     logger.info(f"Updating profile with: {args}")
                     update_profile_db(args)
                     messages.append({
                        'role': 'tool',
                        'content': "User profile updated successfully.",
                     })
                else:
                    logger.warning(f"Unknown tool requested: {fn_name}")
                    messages.append({
                        'role': 'tool',
                        'content': f"Error: Tool '{fn_name}' not found.",
                    })
            
            # Second call: Get final response with tool outputs
            # Force natural language
            messages.append({
                "role": "system",
                "content": "Analyze the above tool outputs. Synthesize a natural language answer for the user. Do not output JSON."
            })
            print("DEBUG: Sending final prompt with tool outputs...")
            final_response = ollama.chat(model=model, messages=messages)
            content = final_response['message']['content']
            print(f"DEBUG: Final content length: {len(content) if content else 0}")
            
            if not content and len(messages) > 2:
                # Fallback: If LLM returns empty but we have tool outputs, use the last tool output
                # This is common for pre-formatted tools like RAG
                print("DEBUG: Empty LLM response. Falling back to raw tool output.")
                last_tool_msg = next((m for m in reversed(messages) if m.get('role') == 'tool'), None)
                if last_tool_msg:
                    raw = last_tool_msg['content']
                    # Attempt to pretty print if it's a known structured format (e.g. from lookup_hardware)
                    if "Mark:" in raw and "Price:" in raw:
                        # It's likely a single hardware result, leave as is, it's already readable
                        return raw
                    if raw.strip().startswith("[") or raw.strip().startswith("{"):
                         # It's JSON (e.g. list of prices). Try to tabularize.
                         try:
                             data = json.loads(raw)
                             if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                 # List of dicts (prices gaming?)
                                 lines = ["**Here is what I found:**"]
                                 for item in data[:5]:
                                     lines.append(f"- **{item.get('title', 'Unknown')}**: {item.get('price_eur', 0)}€ (Score: {item.get('score', 0):.2f})")
                                 return "\n".join(lines)
                         except:
                             pass
                    return raw
            
            return content
            
        else:
            # No tool call, just return content
            if not message['content']:
                print(f"DEBUG: Ollama returned empty content. Message keys: {message.keys()}")
            return message['content']

    except Exception as e:
        print(f"DEBUG: Ollama Exception: {e}")
        logger.error(f"Ollama API error: {e}")
        return "I'm having trouble connecting to my brain. Is Ollama running?"
