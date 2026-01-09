#!/usr/bin/env python3
"""
Test script for chat memory functionality.

This script tests:
1. Creating a chat session
2. Multi-turn conversation with context
3. JSON persistence
4. Session retrieval
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat_memory():
    """Test the chat memory functionality."""
    print("=" * 60)
    print("Testing Chat Memory with JSON Persistence")
    print("=" * 60)
    
    # Test 1: First message (create session)
    print("\n1. Sending first message: 'give me the most important issue to fix'")
    response1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "give me the most important issue to fix"
        }
    )
    
    if response1.status_code != 200:
        print(f"❌ Error: {response1.status_code}")
        print(response1.text)
        return False
    
    data1 = response1.json()
    session_id = data1.get("session_id")
    print(f"✓ Session created: {session_id}")
    print(f"Response: {data1.get('response', '')[:200]}...")
    
    # Test 2: Follow-up message (should reference previous context)
    print(f"\n2. Sending follow-up: 'how can I fix this issue?'")
    time.sleep(1)  # Brief pause
    
    response2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "how can I fix this issue?",
            "session_id": session_id
        }
    )
    
    if response2.status_code != 200:
        print(f"❌ Error: {response2.status_code}")
        print(response2.text)
        return False
    
    data2 = response2.json()
    print(f"✓ Session continued: {data2.get('session_id')}")
    print(f"Response: {data2.get('response', '')[:200]}...")
    
    # Test 3: Retrieve session list
    print(f"\n3. Retrieving session list")
    response3 = requests.get(f"{BASE_URL}/chat/sessions")
    
    if response3.status_code != 200:
        print(f"❌ Error: {response3.status_code}")
        return False
    
    sessions = response3.json().get("sessions", [])
    print(f"✓ Found {len(sessions)} session(s)")
    
    if sessions:
        latest = sessions[0]
        print(f"  Latest session: {latest.get('session_id')}")
        print(f"  Messages: {latest.get('message_count')}")
        print(f"  Models: {latest.get('models_used')}")
    
    # Test 4: Retrieve full session
    print(f"\n4. Retrieving full session: {session_id}")
    response4 = requests.get(f"{BASE_URL}/chat/sessions/{session_id}")
    
    if response4.status_code != 200:
        print(f"❌ Error: {response4.status_code}")
        return False
    
    session_data = response4.json()
    print(f"✓ Session retrieved")
    print(f"  Created: {session_data.get('created_at')}")
    print(f"  Last access: {session_data.get('last_access')}")
    print(f"  Total messages: {len(session_data.get('messages', []))}")
    print(f"  Models used: {session_data.get('metadata', {}).get('models_used')}")
    
    # Display conversation
    print("\n  Conversation:")
    for i, msg in enumerate(session_data.get('messages', []), 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100]
        print(f"    {i}. [{role}] {content}...")
    
    # Test 5: Verify JSON file exists
    print(f"\n5. Verifying JSON file persistence")
    import os
    json_file = f"chat_logs/session_{session_id}.json"
    
    if os.path.exists(json_file):
        print(f"✓ JSON file exists: {json_file}")
        with open(json_file, 'r') as f:
            file_data = json.load(f)
            print(f"  File size: {os.path.getsize(json_file)} bytes")
            print(f"  Messages in file: {len(file_data.get('messages', []))}")
    else:
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_chat_memory()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running: cd backend && python -m uvicorn app:app --reload")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
