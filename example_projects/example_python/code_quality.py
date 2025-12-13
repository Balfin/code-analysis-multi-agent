"""
Code Quality Issues Example - Contains intentionally poor code for testing.
"""

import os
import sys
import json
import random  # Issue: Unused import
import datetime  # Issue: Unused import
from collections import defaultdict  # Issue: Unused import


# Issue: Global mutable state
global_data = []
COUNTER = 0


def a(x, y, z):
    """Issue: Poor function naming and no docstring clarity."""
    # Issue: Magic numbers
    return x * 1.0825 + y * 0.0725 - z * 3.14159


def calculate_something(data, flag1, flag2, flag3, option1, option2, extra, more, stuff):
    """Issue: Too many parameters."""
    result = 0
    for item in data:
        if flag1:
            result += item
        if flag2:
            result -= item
        if flag3:
            result *= item
    return result


def process_user_data(user):
    """Function with multiple issues."""
    # Issue: Unused variable
    unused_var = "this is never used"
    
    # Issue: Variable shadowing built-in
    list = user.get("items", [])
    dict = user.get("metadata", {})
    str = user.get("name", "")
    
    # Issue: Redundant comparison
    if user.get("active") == True:
        pass
    
    # Issue: Comparing to None incorrectly
    if user.get("email") == None:
        return None
    
    # Issue: Empty except block
    try:
        result = int(user.get("age"))
    except:
        pass
    
    return list, dict, str


class badlyNamedClass:
    """Issue: Class naming doesn't follow PascalCase convention."""
    
    # Issue: Class attribute with mutable default
    shared_list = []
    
    def __init__(self, Value, OTHER_VALUE):
        """Issue: Parameter naming inconsistent."""
        self.Value = Value
        self.OTHER_VALUE = OTHER_VALUE
        self.data = None
    
    def DO_SOMETHING(self):
        """Issue: Method naming doesn't follow snake_case."""
        # Issue: Using global keyword
        global COUNTER
        COUNTER += 1
        
        # Issue: Dead code - unreachable
        return self.Value
        print("This will never execute")
    
    def method_with_side_effects(self):
        """Issue: Hidden side effect - modifying class attribute."""
        self.shared_list.append("item")
        global_data.append("global item")


def deeply_nested_function(data):
    """Issue: Excessive nesting depth."""
    result = []
    if data:
        for item in data:
            if item.get("active"):
                for sub_item in item.get("children", []):
                    if sub_item.get("valid"):
                        for value in sub_item.get("values", []):
                            if value > 0:
                                if value < 100:
                                    if value % 2 == 0:
                                        result.append(value)
    return result


def duplicate_code_example_1(items):
    """Issue: Code duplication - similar to duplicate_code_example_2."""
    total = 0
    for item in items:
        if item.get("type") == "A":
            total += item.get("value", 0) * 1.1
        elif item.get("type") == "B":
            total += item.get("value", 0) * 1.2
        elif item.get("type") == "C":
            total += item.get("value", 0) * 1.3
    return total


def duplicate_code_example_2(items):
    """Issue: Code duplication - similar to duplicate_code_example_1."""
    total = 0
    for item in items:
        if item.get("type") == "A":
            total += item.get("value", 0) * 1.1
        elif item.get("type") == "B":
            total += item.get("value", 0) * 1.2
        elif item.get("type") == "C":
            total += item.get("value", 0) * 1.3
    return total * 2  # Only difference


def overly_complex_function(x, y, z, a, b):
    """Issue: High cyclomatic complexity."""
    result = 0
    
    if x > 0:
        if y > 0:
            result = x + y
        elif y < 0:
            result = x - y
        else:
            result = x
    elif x < 0:
        if y > 0:
            result = y - x
        elif y < 0:
            result = -(x + y)
        else:
            result = -x
    else:
        if y > 0:
            result = y
        elif y < 0:
            result = -y
        else:
            result = 0
    
    if z:
        result *= 2
    if a:
        result += 10
    if b:
        result -= 5
    
    return result


# Issue: Multiple statements on one line
x = 1; y = 2; z = 3

# Issue: Star imports (if this were in actual use)
# from module import *


def function_with_no_return_type_hints(data, config, options):
    """Issue: No type hints."""
    processed = []
    for item in data:
        if config.get("transform"):
            item = item.upper()
        processed.append(item)
    return processed


def long_function_that_does_too_much(user_data, config, options, output_format):
    """Issue: Function doing too many things - violates single responsibility."""
    # Validate user data
    if not user_data:
        return None
    if not user_data.get("name"):
        return None
    if not user_data.get("email"):
        return None
    
    # Transform user data
    name = user_data["name"].strip().title()
    email = user_data["email"].strip().lower()
    
    # Apply configuration
    if config.get("anonymize"):
        email = "***@***.***"
    
    # Format output
    if output_format == "json":
        return json.dumps({"name": name, "email": email})
    elif output_format == "csv":
        return f"{name},{email}"
    elif output_format == "xml":
        return f"<user><name>{name}</name><email>{email}</email></user>"
    else:
        return {"name": name, "email": email}

