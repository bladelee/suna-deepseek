import json
import os
from datetime import datetime
from pathlib import Path

class SessionStateManager:
    def __init__(self, state_file=".claude/session_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
    
    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._default_state()
        return self._default_state()
    
    def _default_state(self):
        return {
            "last_session": {
                "timestamp": datetime.now().isoformat(),
                "todos": [],
                "current_file": None,
                "progress_notes": ""
            },
            "session_history": []
        }
    
    def save_state(self, todos, current_file=None, progress_notes=""):
        self.state["last_session"] = {
            "timestamp": datetime.now().isoformat(),
            "todos": todos,
            "current_file": current_file,
            "progress_notes": progress_notes
        }
        
        # Keep last 10 sessions in history
        if len(self.state["session_history"]) >= 10:
            self.state["session_history"].pop(0)
        self.state["session_history"].append(self.state["last_session"].copy())
        
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_last_state(self):
        return self.state["last_session"]
    
    def get_session_history(self):
        return self.state["session_history"]

# Usage example:
# manager = SessionStateManager()
# manager.save_state(todos, current_file, progress_notes)
# last_state = manager.load_last_state()