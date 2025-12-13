"""
Security Issues Example - Contains intentionally vulnerable code for testing.
DO NOT USE IN PRODUCTION!
"""

import os
import pickle
import subprocess
import sqlite3
import hashlib

# Issue: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "super_secret_token_12345"


def connect_to_database(user_input):
    """SQL Injection vulnerability - user input directly in query."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Issue: SQL Injection - directly concatenating user input
    query = "SELECT * FROM users WHERE username = '" + user_input + "'"
    cursor.execute(query)
    
    # Issue: Another SQL injection variant
    cursor.execute(f"DELETE FROM logs WHERE user_id = {user_input}")
    
    return cursor.fetchall()


def run_system_command(user_command):
    """Command injection vulnerability."""
    # Issue: Command injection - executing user input directly
    os.system(user_command)
    
    # Issue: Another command injection via subprocess
    subprocess.call(user_command, shell=True)
    
    # Issue: Using eval on user input
    result = eval(user_command)
    return result


def unsafe_deserialization(data):
    """Insecure deserialization vulnerability."""
    # Issue: Pickle deserialization of untrusted data
    return pickle.loads(data)


def weak_password_hash(password):
    """Using weak hashing algorithms."""
    # Issue: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


def insecure_random():
    """Using insecure random number generation."""
    import random
    # Issue: Using random instead of secrets for security-sensitive operations
    token = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    return token


class UserAuth:
    """Authentication class with security issues."""
    
    # Issue: Hardcoded admin credentials
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "password123"
    
    def __init__(self):
        # Issue: Storing password in plain text
        self.users = {
            "john": "john_password",
            "jane": "jane_secret",
            "bob": "bob12345"
        }
    
    def authenticate(self, username, password):
        """Insecure authentication."""
        # Issue: Timing attack vulnerability - early return reveals username validity
        if username not in self.users:
            return False
        
        # Issue: Plain text password comparison
        if self.users[username] == password:
            return True
        return False
    
    def change_password(self, username, old_pass, new_pass):
        """Password change with no validation."""
        # Issue: No password strength validation
        # Issue: No rate limiting
        # Issue: Logging sensitive information
        print(f"User {username} changing password from {old_pass} to {new_pass}")
        self.users[username] = new_pass


def read_file(filename):
    """Path traversal vulnerability."""
    # Issue: No path validation - allows directory traversal
    base_path = "/var/www/uploads/"
    full_path = base_path + filename  # Allows "../../../etc/passwd"
    
    with open(full_path, 'r') as f:
        return f.read()


def create_temp_file(content):
    """Insecure temporary file creation."""
    # Issue: Predictable temporary file name
    temp_file = "/tmp/app_temp_" + str(os.getpid())
    
    # Issue: World-readable permissions
    with open(temp_file, 'w') as f:
        f.write(content)
    
    return temp_file

