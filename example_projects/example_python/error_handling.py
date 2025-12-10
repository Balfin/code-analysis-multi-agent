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


def broad_exception_handler(filename):
    """Issue: Catching overly broad Exception."""
    try:
        with open(filename, 'r') as f:
            data = f.read()
        return json.loads(data)
    except Exception as e:  # Issue: Too broad - should catch specific exceptions
        print(f"Error: {e}")
        return None


def silent_failure(user_id):
    """Issue: Silently swallowing exceptions."""
    try:
        user = fetch_user(user_id)
        return user
    except Exception:
        pass  # Issue: Silent failure - no logging, no indication of error
    
    return None


def exception_as_flow_control(items):
    """Issue: Using exceptions for normal flow control."""
    result = []
    for item in items:
        try:
            # Issue: Using try/except instead of checking first
            value = int(item)
            result.append(value)
        except ValueError:
            # This is expected for non-numeric items - shouldn't use exceptions
            continue
    return result


def ignoring_specific_error_info(data):
    """Issue: Losing important error information."""
    try:
        processed = process_data(data)
        return processed
    except ValueError:
        # Issue: Not preserving original exception context
        raise RuntimeError("Processing failed")


def inconsistent_error_handling(filename, fallback=None):
    """Issue: Inconsistent error handling patterns."""
    # Sometimes returns None
    if not filename:
        return None
    
    # Sometimes raises exception
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    try:
        with open(filename) as f:
            return f.read()
    except IOError:
        # Sometimes returns fallback
        return fallback


def no_error_handling(filename):
    """Issue: No error handling at all for risky operations."""
    # Issue: No handling for FileNotFoundError, PermissionError, etc.
    with open(filename, 'r') as f:
        data = f.read()
    
    # Issue: No handling for JSONDecodeError
    parsed = json.loads(data)
    
    # Issue: No handling for KeyError
    return parsed["required_field"]["nested_value"]


def error_handling_with_side_effects(resources):
    """Issue: Cleanup code might not run on exception."""
    connection = open_connection()
    file_handle = open("temp.txt", "w")
    
    # Issue: If process_resources raises, cleanup doesn't happen
    result = process_resources(resources)
    
    connection.close()  # Might not execute
    file_handle.close()  # Might not execute
    
    return result


def poor_finally_usage():
    """Issue: Return in finally block."""
    try:
        result = risky_operation()
        return result
    except Exception:
        return None
    finally:
        # Issue: Return in finally silently overwrites other returns
        return "always this"


def exception_in_exception_handler():
    """Issue: Code in except block can also raise."""
    try:
        result = risky_operation()
    except Exception as e:
        # Issue: Logging might fail and mask the original error
        log_error_to_file(e)  # What if this raises?
        send_error_notification(e)  # What if this raises?
        raise


def missing_exception_chaining(data):
    """Issue: Not using exception chaining (from)."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # Issue: Should use 'raise ... from e' to preserve context
        raise ValueError("Invalid data format")


def catching_and_reraising_same(data):
    """Issue: Pointless catch and re-raise."""
    try:
        return process_data(data)
    except ValueError:
        # Issue: This adds nothing useful
        raise


def string_exception_check(error):
    """Issue: Checking exception type by string matching."""
    try:
        result = risky_operation()
    except Exception as e:
        # Issue: Should use isinstance, not string matching
        if "ValueError" in str(type(e)):
            return "value error"
        elif "KeyError" in str(type(e)):
            return "key error"
        raise


class ResourceManager:
    """Class with error handling issues."""
    
    def __init__(self):
        self.resources = []
    
    def acquire_resources(self, count):
        """Issue: Partial acquisition without cleanup on failure."""
        for i in range(count):
            # Issue: If acquisition fails mid-way, previous resources leak
            resource = acquire_expensive_resource(i)
            self.resources.append(resource)
    
    def process(self):
        """Issue: No try/finally for cleanup."""
        for resource in self.resources:
            use_resource(resource)
        # Issue: If use_resource raises, cleanup never happens
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        for resource in self.resources:
            release_resource(resource)
        self.resources = []


# Helper functions (stubs for the examples)
def fetch_user(user_id):
    raise ValueError("User not found")


def process_data(data):
    return data


def open_connection():
    return "connection"


def process_resources(resources):
    return resources


def risky_operation():
    return "result"


def log_error_to_file(error):
    pass


def send_error_notification(error):
    pass


def acquire_expensive_resource(index):
    return f"resource_{index}"


def use_resource(resource):
    pass


def release_resource(resource):
    pass
