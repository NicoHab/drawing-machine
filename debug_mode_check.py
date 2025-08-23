#!/usr/bin/env python3
"""
Debug script to test mode checking logic
"""
from pathlib import Path

def get_system_mode():
    """Get current system mode from file."""
    try:
        mode_file = Path(__file__).parent / "system_mode.txt"
        print(f"Looking for mode file at: {mode_file}")
        print(f"File exists: {mode_file.exists()}")
        
        if mode_file.exists():
            with open(mode_file, 'r') as f:
                mode = f.read().strip()
                print(f"Read mode: '{mode}' (length: {len(mode)})")
                print(f"Mode bytes: {mode.encode()}")
                return mode
        print("Mode file doesn't exist, defaulting to auto")
        return "auto"
    except Exception as e:
        print(f"Error reading mode file: {e}")
        return "auto"

if __name__ == "__main__":
    print("Testing mode checking logic...")
    mode = get_system_mode()
    print(f"Final mode: '{mode}'")
    print(f"Mode == 'manual': {mode == 'manual'}")
    print(f"Mode == 'auto': {mode == 'auto'}")