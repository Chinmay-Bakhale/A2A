"""
Integration test with comprehensive coverage
Run this after installing dependencies to test the complete system
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8080"


def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")


def test_stats():
    """Test stats endpoint"""
    print("\n=== Testing Stats Endpoint ===")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Stats endpoint passed")


def test_metrics():
    """Test Prometheus metrics endpoint"""
    print("\n=== Testing Metrics Endpoint ===")
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    # Check for key metrics
    content = response.text
    assert "leave_assistant_requests_total" in content
    assert "leave_assistant_agent_responses_total" in content
    assert "leave_assistant_tool_calls_total" in content
    
    print("✅ Metrics endpoint passed")
    print(f"Sample metrics:\n{content[:500]}...")


def test_basic_chat():
    """Test basic chat functionality"""
    print("\n=== Testing Basic Chat ===")
    
    payload = {
        "message": "Hello! Can you help me understand leave policies?",
        "session_id": "integration-test-1"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:200]}...")
        print(f"Session ID: {data['session_id']}")
        assert data['session_id'] == "integration-test-1"
        print("✅ Basic chat passed")
    else:
        print(f"❌ Chat failed: {response.text}")


def test_leave_balance_tool():
    """Test leave balance checking with tool calling"""
    print("\n=== Testing Leave Balance Tool ===")
    
    payload = {
        "message": "What is the leave balance for employee EMP001?",
        "session_id": "integration-test-2"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        
        # Response should mention the balance
        assert any(word in data['response'].lower() for word in ['balance', 'days', 'pto'])
        print("✅ Leave balance tool passed")
    else:
        print(f"❌ Tool call failed: {response.text}")
    
    time.sleep(15)  # Rate limit handling


def test_policy_inquiry():
    """Test policy details retrieval"""
    print("\n=== Testing Policy Inquiry ===")
    
    payload = {
        "message": "What is the PTO policy for US employees?",
        "session_id": "integration-test-3"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:300]}...")
        
        # Response should mention PTO details
        assert any(word in data['response'].lower() for word in ['pto', 'policy', 'days'])
        print("✅ Policy inquiry passed")
    else:
        print(f"❌ Policy inquiry failed: {response.text}")
    
    time.sleep(15)  # Rate limit handling


def test_eligibility_check():
    """Test leave eligibility calculation"""
    print("\n=== Testing Eligibility Check ===")
    
    payload = {
        "message": "Can employee EMP001 take 5 days of PTO from March 1 to March 5, 2026?",
        "session_id": "integration-test-4"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        
        # Response should mention eligibility
        assert any(word in data['response'].lower() for word in ['eligible', 'approve', 'balance'])
        print("✅ Eligibility check passed")
    else:
        print(f"❌ Eligibility check failed: {response.text}")


def test_session_delete():
    """Test session deletion"""
    print("\n=== Testing Session Deletion ===")
    
    # Create a session first
    payload = {
        "message": "Test message",
        "session_id": "delete-test-session"
    }
    requests.post(f"{BASE_URL}/chat", json=payload)
    
    # Delete it
    response = requests.delete(f"{BASE_URL}/session/delete-test-session")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
        print("✅ Session deletion passed")
    else:
        print(f"❌ Session deletion failed: {response.text}")


def main():
    """Run all integration tests"""
    print("🚀 Starting Integration Tests")
    print("=" * 60)
    
    try:
        # Non-LLM tests (no rate limits)
        test_health()
        test_stats()
        test_metrics()
        
        # LLM-based tests (with rate limit handling)
        test_basic_chat()
        time.sleep(15)
        
        test_leave_balance_tool()
        test_policy_inquiry()
        test_eligibility_check()
        test_session_delete()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Is it running?")
        print("Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
