"""
Quick single test - use this to test one query at a time
Avoids rate limit issues

Usage: python quick_test.py
"""

import requests
import json


def test_single_query():
    """Test a single query"""
    
    BASE_URL = "http://localhost:8080"
    
    print("\n" + "="*60)
    print("  QUICK TEST - Single Query")
    print("="*60 + "\n")
    
    # Customize your test here
    payload = {
        "message": "How many PTO days do I have left?",
        "session_id": "quick-test",
        "employee_id": "EMP001"
    }
    
    print(f"📤 Sending request:")
    print(f"   Message: {payload['message']}")
    print(f"   Employee: {payload['employee_id']}\n")
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        
        print(f"📥 Response:")
        print(f"   Status: {response.status_code}")
        
        data = response.json()
        print(f"\n💬 Agent Response:")
        print(f"   {data['response']}\n")
        
        if 'metadata' in data:
            print(f"📊 Metadata:")
            print(json.dumps(data['metadata'], indent=2))
        
        return data
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("Make sure the server is running on port 8080")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Test 1: Check balance
    print("\n🧪 Test 1: Check Leave Balance")
    test_single_query()
    
    # Uncomment below for more tests (run one at a time to avoid rate limits)
    
    # print("\n🧪 Test 2: Policy Inquiry")
    # payload = {
    #     "message": "What's the PTO policy for US employees?",
    #     "session_id": "quick-test-2",
    #     "employee_id": "EMP001"
    # }
    # test_single_query()
    
    # print("\n🧪 Test 3: Eligibility Check")
    # payload = {
    #     "message": "Can I take 5 days off from June 1-5, 2024?",
    #     "session_id": "quick-test-3",
    #     "employee_id": "EMP001"
    # }
    # test_single_query()
