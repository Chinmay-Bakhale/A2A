"""
Quick test script to verify the application works
Run this to test locally before deploying

Usage: python test_local.py
"""

import requests
import json
import time
from datetime import datetime


BASE_URL = "http://localhost:8080"


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint"""
    print_section("Testing Health Endpoint")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Health check failed!"
    print("✅ Health check passed!")


def test_chat_basic():
    """Test basic chat interaction"""
    print_section("Testing Basic Chat")
    
    payload = {
        "message": "Hello! Can you help me?",
        "session_id": "test-session-1",
        "employee_id": "EMP001"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Chat request failed!"
    print("✅ Basic chat passed!")
    
    # Wait to avoid rate limits
    print("⏳ Waiting 15s to avoid rate limits...")
    time.sleep(15)


def test_check_leave_balance():
    """Test checking leave balance"""
    print_section("Testing Leave Balance Check")
    
    payload = {
        "message": "How many PTO days do I have left?",
        "session_id": "test-session-2",
        "employee_id": "EMP001"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Balance check failed!"
    print("✅ Leave balance check passed!")
    
    # Wait to avoid rate limits
    print("⏳ Waiting 15s to avoid rate limits...")
    time.sleep(15)


def test_eligibility_check():
    """Test leave eligibility checking"""
    print_section("Testing Leave Eligibility")
    
    payload = {
        "message": "Can I take 5 days of PTO from 2024-06-01 to 2024-06-05?",
        "session_id": "test-session-3",
        "employee_id": "EMP001"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Eligibility check failed!"
    print("✅ Eligibility check passed!")
    
    # Wait to avoid rate limits
    print("⏳ Waiting 15s to avoid rate limits...")
    time.sleep(15)


def test_policy_inquiry():
    """Test policy information retrieval"""
    print_section("Testing Policy Inquiry")
    
    payload = {
        "message": "What are the PTO policies for US employees?",
        "session_id": "test-session-4",
        "employee_id": "EMP001"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Wait to avoid rate limits
    print("⏳ Waiting 15s to avoid rate limits...")
    time.sleep(15)
    
    assert response.status_code == 200, "Policy inquiry failed!"
    print("✅ Policy inquiry passed!")


def test_stats():
    """Test stats endpoint"""
    print_section("Testing Stats Endpoint")
    
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Stats check failed!"
    print("✅ Stats check passed!")


def test_multi_turn_conversation():
    """Test multi-turn conversation"""
    print_section("Testing Multi-turn Conversation")
    
    session_id = "test-session-multiturn"
    
    # Turn 1
    print("\n--- Turn 1 ---")
    payload1 = {
        "message": "Hi, I'm planning a vacation",
        "session_id": session_id,
        "employee_id": "EMP001"
    }
    response1 = requests.post(f"{BASE_URL}/chat", json=payload1)
    print(f"User: {payload1['message']}")
    print(f"Agent: {response1.json()['response']}")
    time.sleep(15)  # Wait for rate limit
    
    # Turn 2
    print("\n--- Turn 2 ---")
    payload2 = {
        "message": "How many PTO days can I take?",
        "session_id": session_id,
        "employee_id": "EMP001"
    }
    response2 = requests.post(f"{BASE_URL}/chat", json=payload2)
    print(f"User: {payload2['message']}")
    print(f"Agent: {response2.json()['response']}")
    time.sleep(15)  # Wait for rate limit
    
    # Turn 3
    print("\n--- Turn 3 ---")
    payload3 = {
        "message": "Can I take them in December?",
        "session_id": session_id,
        "employee_id": "EMP001"
    }
    response3 = requests.post(f"{BASE_URL}/chat", json=payload3)
    print(f"User: {payload3['message']}")
    print(f"Agent: {response3.json()['response']}")
    
    print("\n✅ Multi-turn conversation passed!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  LEAVE POLICY ASSISTANT - LOCAL TESTING")
    print("="*60)
    print(f"\nTesting server at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test endpoints
        test_health()
        test_chat_basic()
        test_check_leave_balance()
        test_eligibility_check()
        test_policy_inquiry()
        test_stats()
        test_multi_turn_conversation()
        
        # Summary
        print_section("TEST SUMMARY")
        print("✅ All tests passed successfully!")
        print("\nYour Leave Policy Assistant is working correctly!")
        print(f"\nAPI Documentation: {BASE_URL}/docs")
        print(f"Alternative Docs: {BASE_URL}/redoc")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the server")
        print(f"Please make sure the server is running on {BASE_URL}")
        print("\nStart the server with:")
        print("  python -m uvicorn app.main:app --reload --port 8080")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
