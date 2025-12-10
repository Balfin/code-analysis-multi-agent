"""
Style Issues Example - Contains intentionally poor code style for testing.
"""

import os,sys,json  # Issue: Multiple imports on one line

# Issue: Inconsistent spacing
x=1
y = 2
z  =  3

# Issue: Lines too long - exceeds PEP 8's 79 character recommendation
def function_with_extremely_long_name_that_violates_line_length_guidelines_and_makes_code_hard_to_read(parameter_one, parameter_two, parameter_three, parameter_four):
    return parameter_one + parameter_two + parameter_three + parameter_four


# Issue: Inconsistent quotes
string_single = 'single quotes'
string_double = "double quotes"
string_mixed = 'mixing "quotes" is ' + "inconsistent"


# Issue: Missing blank lines between top-level definitions
def function_one():
    pass
def function_two():
    pass
def function_three():
    pass


class poorly_formatted_class:  # Issue: Class name not PascalCase
    """Issue: Inconsistent indentation and formatting throughout."""
    
    def __init__(self,name,value):  # Issue: No spaces after commas
        self.name=name  # Issue: No spaces around =
        self.value = value
    
    def method_one( self ):  # Issue: Spaces inside parentheses
        return self.name
    
    def method_two(self):
      return self.value  # Issue: Wrong indentation (2 spaces instead of 4)
    
    def method_three(self):
            return self.name + self.value  # Issue: Wrong indentation (12 spaces)


# Issue: Trailing whitespace (represented here conceptually)
def function_with_trailing_whitespace():    
    result = 1 + 2    
    return result    


# Issue: No docstring
def undocumented_function(arg1, arg2, arg3):
    complex_result = (arg1 * arg2 + arg3) / (arg1 - arg2)
    return complex_result


# Issue: Inconsistent naming conventions
def camelCaseFunction():  # Should be snake_case
    pass

def snake_case_function():
    pass

def MixedCase_function():  # Inconsistent
    pass


# Issue: Magic numbers without explanation
def calculate_tax(amount):
    return amount * 0.0825  # What is 0.0825?


def calculate_shipping(weight):
    if weight < 2.5:  # Magic numbers
        return 5.99
    elif weight < 10:
        return 12.99
    elif weight < 50:
        return 24.99
    else:
        return 49.99


# Issue: Commented-out code
def active_function():
    result = compute_value()
    # old_result = legacy_compute()
    # if old_result != result:
    #     log_discrepancy()
    return result


# Issue: TODO comments that have been left indefinitely
def function_with_todos():
    # TODO: Fix this later
    # FIXME: This is broken
    # XXX: Hack - need to refactor
    # HACK: Temporary solution
    return 42


# Issue: Misleading comments
def add_numbers(a, b):
    # Subtract the numbers
    return a + b


def subtract_numbers(a, b):
    """Adds two numbers together."""  # Wrong docstring
    return a - b


# Issue: Multiple statements per line
a = 1; b = 2; c = 3; d = a + b + c

# Issue: Semicolons at end of statements
result = 1 + 2;
another_result = 3 + 4;


# Issue: Inconsistent boolean comparisons
def check_conditions(flag, value, items):
    # Issue: Comparing to True/False explicitly
    if flag == True:
        pass
    
    if flag is False:
        pass
    
    # Issue: Comparing length to 0
    if len(items) == 0:
        pass
    
    if len(items) > 0:
        pass
    
    # Issue: Explicit None comparison with ==
    if value == None:
        pass


# Issue: Using backslash for line continuation instead of parentheses
long_expression = 1 + 2 + 3 + 4 + 5 + \
                  6 + 7 + 8 + 9 + 10


# Issue: Unnecessary parentheses
def unnecessary_parens():
    x = (1)
    y = (1 + 2)
    if (x > 0):
        return (True)
    return (False)


# Issue: f-string not used when it could be
def format_message(name, count):
    # Issue: Using .format() when f-string is cleaner
    message1 = "Hello, {}! You have {} messages.".format(name, count)
    
    # Issue: Using % formatting
    message2 = "Hello, %s! You have %d messages." % (name, count)
    
    # Issue: String concatenation
    message3 = "Hello, " + name + "! You have " + str(count) + " messages."
    
    return message1, message2, message3


class ClassWithBadSpacing:
    """Issue: Inconsistent method spacing."""
    def method_one(self):
        pass

    def method_two(self):
        pass


    def method_three(self):  # Issue: Too many blank lines above
        pass
    def method_four(self):  # Issue: No blank line above
        pass


# Issue: Import not at top of file
import datetime


def late_import_function():
    # Issue: Import inside function (sometimes okay, but often not)
    import random
    return random.randint(1, 100)


# Stub functions for the examples
def compute_value():
    return 1
