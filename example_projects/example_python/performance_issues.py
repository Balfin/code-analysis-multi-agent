"""
Performance Issues Example - Contains intentionally inefficient code for testing.
"""

import time
import re


def inefficient_string_concatenation(items):
    """Issue: String concatenation in loop - O(n²) complexity."""
    result = ""
    for item in items:
        result = result + str(item) + ", "  # Creates new string each iteration
    return result


def inefficient_list_operations(data, item):
    """Issue: Using list for membership testing - O(n) vs O(1) for set."""
    large_list = list(range(100000))
    
    # Issue: O(n) lookup in list
    if item in large_list:
        return True
    
    # Issue: Repeated list lookups
    for d in data:
        if d in large_list:
            print(f"Found {d}")
    
    return False


def repeated_computation(items):
    """Issue: Repeated expensive computation in loop."""
    results = []
    for item in items:
        # Issue: Compiling regex in every iteration
        pattern = re.compile(r'\d+')
        matches = pattern.findall(str(item))
        results.append(matches)
    return results


def inefficient_file_reading(filename):
    """Issue: Reading file multiple times."""
    # Issue: Opening and reading the same file multiple times
    line_count = len(open(filename).readlines())
    word_count = len(open(filename).read().split())
    char_count = len(open(filename).read())
    
    return line_count, word_count, char_count


def memory_inefficient_processing(large_data):
    """Issue: Loading everything into memory at once."""
    # Issue: Creating multiple copies of data
    data_copy1 = list(large_data)
    data_copy2 = [item for item in data_copy1]
    data_copy3 = data_copy2[:]
    
    # Issue: Not using generators
    processed = [expensive_transform(item) for item in data_copy3]
    filtered = [item for item in processed if item > 0]
    final = [item * 2 for item in filtered]
    
    return final


def expensive_transform(item):
    """Simulated expensive operation."""
    time.sleep(0.001)  # Simulate work
    return item * 2


def n_squared_algorithm(items):
    """Issue: O(n²) algorithm where O(n) is possible."""
    result = []
    # Issue: Nested loops for finding duplicates
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in result:
                    result.append(items[i])
    return result


def recursive_without_memoization(n):
    """Issue: Recursive Fibonacci without memoization - exponential time."""
    if n <= 1:
        return n
    # Issue: Recalculating the same values many times
    return recursive_without_memoization(n - 1) + recursive_without_memoization(n - 2)


class InefficientDataStructure:
    """Class with performance issues in data structure usage."""
    
    def __init__(self):
        # Issue: Using list when set would be more efficient for lookups
        self.seen_items = []
        self.data = []
    
    def add_item(self, item):
        """Issue: O(n) duplicate check."""
        # Issue: Linear search for duplicates
        if item not in self.seen_items:
            self.seen_items.append(item)
            self.data.append(item)
    
    def remove_item(self, item):
        """Issue: Multiple O(n) operations."""
        if item in self.seen_items:  # O(n)
            self.seen_items.remove(item)  # O(n)
        if item in self.data:  # O(n)
            self.data.remove(item)  # O(n)
    
    def get_sorted(self):
        """Issue: Sorting every time instead of maintaining sorted order."""
        return sorted(self.data)


def inefficient_database_pattern(users):
    """Issue: N+1 query pattern simulation."""
    results = []
    for user in users:
        # Issue: Making a "query" for each user instead of batch
        user_details = fetch_user_details(user["id"])  # Simulated DB call
        user_orders = fetch_user_orders(user["id"])    # Another call per user
        results.append({
            "user": user_details,
            "orders": user_orders
        })
    return results


def fetch_user_details(user_id):
    """Simulated database fetch."""
    time.sleep(0.01)  # Simulate network latency
    return {"id": user_id, "name": f"User {user_id}"}


def fetch_user_orders(user_id):
    """Simulated database fetch."""
    time.sleep(0.01)  # Simulate network latency
    return [{"order_id": i} for i in range(3)]


def inefficient_sorting(data):
    """Issue: Bubble sort instead of built-in sort."""
    # Issue: Using O(n²) bubble sort
    arr = list(data)
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def unnecessary_work(items):
    """Issue: Doing unnecessary computations."""
    results = []
    for item in items:
        # Issue: Calculating length in every iteration
        total_items = len(items)
        
        # Issue: Creating new list each iteration
        temp_list = list(range(100))
        
        # Issue: Unnecessary type conversion
        result = int(float(str(item)))
        results.append(result)
    
    return results


def blocking_operations(urls):
    """Issue: Sequential blocking operations that could be parallelized."""
    results = []
    for url in urls:
        # Issue: Sequential processing when parallel is possible
        result = simulate_network_request(url)
        results.append(result)
    return results


def simulate_network_request(url):
    """Simulated blocking network request."""
    time.sleep(0.1)  # Simulate network latency
    return f"Response from {url}"
