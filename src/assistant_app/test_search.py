
from assistant_app.adapters.nlu.tools import search_web
import json

def test_search():
    print("Testing search_web('nvidia rtx 5090')...")
    try:
        results = search_web("nvidia rtx 5090")
        print(f"Results type: {type(results)}")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
