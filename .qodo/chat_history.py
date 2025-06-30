import json
import os

def save_chat_history(history, filename="chat_history.json"):
    """Save chat history to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(history, f, indent=4)
        print(f"[DEBUG] Saved chat history to {filename}")
    except Exception as e:
        print(f"[DEBUG] Error saving chat history: {e}")

def load_chat_history(filename="chat_history.json"):
    """Load chat history from a JSON file."""
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                history = json.load(f)
            print(f"[DEBUG] Loaded chat history from {filename}")
            return history
        return []
    except Exception as e:
        print(f"[DEBUG] Error loading chat history: {e}")
        return []

def clear_chat_history(filename="chat_history.json"):
    """Clear chat history by deleting the JSON file."""
    try:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"[DEBUG] Cleared chat history: {filename}")
    except Exception as e:
        print(f"[DEBUG] Error clearing chat history: {e}")