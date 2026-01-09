#!/usr/bin/env python3
"""
Main entry point for the example bad code project.
This file also contains various issues for testing code analysis tools.
"""

import sys
import os

# Issue: Wildcard import (commented for syntax validity, but represents the issue)
# from security_issues import *

from security_issues import connect_to_database, run_system_command, UserAuth
from code_quality import badlyNamedClass, process_user_data, a
from performance_issues import inefficient_string_concatenation, n_squared_algorithm
from error_handling import bare_except_handler, no_error_handling
from style_issues import poorly_formatted_class


# Issue: Global mutable default argument
def configure_app(settings={}):
    """Issue: Mutable default argument."""
    settings["configured"] = True
    return settings


# Issue: Circular dependency potential
def get_module_a():
    from code_quality import global_data
    return global_data


def get_module_b():
    from performance_issues import InefficientDataStructure
    return InefficientDataStructure()


class Application:
    """Main application class with various issues."""
    
    # Issue: Class-level mutable default
    _instances = []
    
    def __init__(self):
        # Issue: Modifying class attribute from instance
        Application._instances.append(self)
        
        # Issue: Hardcoded configuration
        self.debug = True
        self.log_level = "DEBUG"
        self.max_connections = 100
        self.timeout = 30
        
        # Issue: Storing sensitive data in instance
        self.api_key = "hardcoded_api_key_12345"
        self.db_password = "super_secret_password"
    
    def initialize(self):
        """Initialize the application."""
        # Issue: Print statements instead of proper logging
        print("Starting application...")
        print(f"Debug mode: {self.debug}")
        print(f"API Key: {self.api_key}")  # Issue: Logging sensitive data
        
        # Issue: Not using context manager
        self.log_file = open("app.log", "a")
        self.log_file.write("Application initialized\n")
    
    def run(self, user_input):
        """Run the application with user input."""
        # Issue: Direct use of user input without validation
        result = connect_to_database(user_input)
        
        # Issue: eval on user input
        if user_input.startswith("calc:"):
            expression = user_input[5:]
            result = eval(expression)  # Dangerous!
        
        return result
    
    def cleanup(self):
        """Cleanup resources."""
        # Issue: May fail if log_file was never opened
        self.log_file.close()
    
    def __del__(self):
        """Issue: Complex destructor - can cause issues."""
        # Issue: Destructors shouldn't do complex operations
        try:
            self.cleanup()
        except:
            pass  # Issue: Bare except in destructor


def process_batch(items, processor=None):
    """Process a batch of items."""
    # Issue: None check done incorrectly
    if processor == None:
        processor = lambda x: x
    
    results = []
    for i in range(0, len(items)):  # Issue: Should use enumerate
        item = items[i]
        try:
            result = processor(item)
            results.append(result)
        except:  # Issue: Bare except
            results.append(None)
    
    return results


def main():
    """Main function with issues."""
    # Issue: Magic numbers
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Issue: Long if-elif chain instead of dictionary dispatch
    if command == "run":
        app = Application()
        app.initialize()
        if len(sys.argv) > 2:
            result = app.run(sys.argv[2])
            print(result)
    elif command == "test":
        # Issue: Duplicate code
        app = Application()
        app.initialize()
        print("Running tests...")
    elif command == "demo":
        # Issue: Duplicate code
        app = Application()
        app.initialize()
        print("Running demo...")
    elif command == "benchmark":
        # Issue: Duplicate code
        app = Application()
        app.initialize()
        print("Running benchmark...")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


# Issue: Code at module level that runs on import
print("Module loaded")
_config = configure_app()

if __name__ == "__main__":
    main()



