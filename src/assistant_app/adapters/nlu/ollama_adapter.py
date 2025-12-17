import ollama
import logging
import json
from assistant_app.config.settings import settings
from assistant_app.adapters.tools import AVAILABLE_TOOLS

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
                        "description": "The product name to search for.",
                    },
                },
                "required": ["product"],
            },
        },
    },
]

def ask_ollama(text: str) -> str | None:
    """
    Sends a prompt to Ollama, handling potential tool calls.
    """
    model = settings.OLLAMA_MODEL
    
    system_prompt = (
        "You are JARVIS, a helpful assistant and hardware expert. "
        "You have access to tools for looking up hardware benchmarks (PassMark) and detailed specs (VRAM, TDP). "
        "IMPORTANT RULES:\n"
        "1. For PERFORMANCE scores/ranks, use 'lookup_hardware' for EACH item.\n"
        "2. For DETAILED SPECS (VRAM, Cores, TDP), use 'lookup_detailed_specs' for EACH item.\n"
        "3. Do not guess specs or scores. Use the tools."
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
                    
                    # Add tool result to messages
                    messages.append({
                        'role': 'tool',
                        'content': str(tool_output),
                    })
                else:
                    logger.warning(f"Unknown tool requested: {fn_name}")
                    messages.append({
                        'role': 'tool',
                        'content': f"Error: Tool '{fn_name}' not found.",
                    })
            
            # Second call: Get final response with tool outputs
            final_response = ollama.chat(model=model, messages=messages)
            return final_response['message']['content']
            
        else:
            # No tool call, just return content
            return message['content']

    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return "I'm having trouble connecting to my brain. Is Ollama running?"
