"""
Error Handling Issues Example - Contains intentionally poor error handling for testing.
"""

import json
import os


def bare_except_handler(data):
    """Issue: Using bare except clause."""
    try:
        result = json.loads(data)
        return result
    except:  # Issue: Catches everything including KeyboardInterrupt, SystemExit
        return None


def no_error_handling(filename):
    """Issue: No error handling at all for risky operations."""
    # Issue: No handling for FileNotFoundError, PermissionError, etc.
    with open(filename, 'r') as f:
        data = f.read()
    
    # Issue: No handling for JSONDecodeError
    parsed = json.loads(data)
    
    # Issue: No handling for KeyError
    return parsed["required_field"]["nested_value"]
