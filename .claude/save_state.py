#!/usr/bin/env python3
"""
Save current session state to persistent storage
Usage: python .claude/save_state.py "progress notes"
"""

import sys
import json
from session_manager import SessionStateManager

def save_current_state(progress_notes=""):
    manager = SessionStateManager()
    
    # Read current todos from CLI if available
    todos = []
    try:
        # This would need integration with Claude's todo system
        # For now, we'll use a simple approach
        todos = ["Manual todo tracking - use git commits for better persistence"]
    except:
        pass
    
    manager.save_state(todos, progress_notes=progress_notes)
    print(f"Session state saved at {manager.state['last_session']['timestamp']}")

if __name__ == "__main__":
    progress_notes = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    save_current_state(progress_notes)