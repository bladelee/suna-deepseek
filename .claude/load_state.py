#!/usr/bin/env python3
"""
Load last session state from persistent storage
"""

from session_manager import SessionStateManager

def load_last_state():
    manager = SessionStateManager()
    last_state = manager.load_last_state()
    
    print("=== Last Session State ===")
    print(f"Timestamp: {last_state['timestamp']}")
    print(f"Progress: {last_state.get('progress_notes', 'No notes')}")
    print(f"Current File: {last_state.get('current_file', 'None')}")
    
    if last_state.get('todos'):
        print("\nTodos:")
        for i, todo in enumerate(last_state['todos'], 1):
            print(f"  {i}. {todo}")
    
    return last_state

if __name__ == "__main__":
    load_last_state()