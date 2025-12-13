"""
Code Quality Issues Example - Contains intentionally poor code for testing.
"""

import os
import sys
import json
import random  # Issue: Unused import
import datetime  # Issue: Unused import


# Issue: Global mutable state
global_data = []


def a(x, y, z):
    """Issue: Poor function naming and no docstring clarity."""
    return x * 1.0825 + y * 0.0725 - z * 3.14159


def process_user_data(user):
    """Function with multiple issues."""
    # Issue: Variable shadowing built-in
    list = user.get("items", [])
    str = user.get("name", "")
    
    # Issue: Empty except block
    try:
        result = int(user.get("age"))
    except:
        pass
    
    return list, str


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
