"""
Simple test file to verify core functionality
Run with: python -m pytest tests/test_tools.py -v
"""

import pytest
from app.tools import check_leave_balance, calculate_eligibility, get_leave_policy_details


class TestCheckLeaveBalance:
    """Test leave balance checking functionality"""
    
    def test_check_balance_valid_employee(self):
        """Test checking balance for valid employee"""
        result = check_leave_balance("EMP001", "PTO")
        
        assert result["success"] is True
        assert result["employee_id"] == "EMP001"
        assert result["leave_type"] == "PTO"
        assert "balance" in result
    
    def test_check_balance_invalid_employee(self):
        """Test checking balance for non-existent employee"""
        result = check_leave_balance("EMP999")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    def test_check_balance_all_types(self):
        """Test checking all leave balances"""
        result = check_leave_balance("EMP001")
        
        assert result["success"] is True
        assert "all_balances" in result
        assert isinstance(result["all_balances"], dict)


class TestCalculateEligibility:
    """Test leave eligibility calculations"""
    
    def test_eligibility_sufficient_balance(self):
        """Test eligibility with sufficient balance"""
        result = calculate_eligibility(
            employee_id="EMP001",
            leave_type="PTO",
            start_date="2024-06-01",
            end_date="2024-06-05",
            num_days=5
        )
        
        assert result["eligible"] is True
        assert result["requested_days"] == 5
    
    def test_eligibility_insufficient_balance(self):
        """Test eligibility with insufficient balance"""
        result = calculate_eligibility(
            employee_id="EMP001",
            leave_type="PTO",
            start_date="2024-06-01",
            end_date="2024-06-30",
            num_days=25  # More than available
        )
        
        assert result["eligible"] is False
        assert "insufficient" in result["reason"].lower()
    
    def test_eligibility_invalid_leave_type(self):
        """Test eligibility with invalid leave type"""
        result = calculate_eligibility(
            employee_id="EMP001",
            leave_type="Invalid Leave",
            start_date="2024-06-01",
            end_date="2024-06-05",
            num_days=5
        )
        
        assert result["eligible"] is False


class TestGetPolicyDetails:
    """Test policy retrieval functionality"""
    
    def test_get_policy_valid_country(self):
        """Test getting policy for valid country"""
        result = get_leave_policy_details("US", "PTO")
        
        assert result["success"] is True
        assert result["country"] == "US"
        assert result["leave_type"] == "PTO"
        assert "policy" in result
    
    def test_get_policy_invalid_country(self):
        """Test getting policy for invalid country"""
        result = get_leave_policy_details("Invalid")
        
        assert result["success"] is False
    
    def test_get_all_policies_for_country(self):
        """Test getting all policies for a country"""
        result = get_leave_policy_details("India")
        
        assert result["success"] is True
        assert "all_policies" in result
        assert isinstance(result["all_policies"], dict)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def test_circuit_breaker_import(self):
        """Test circuit breaker can be imported"""
        from app.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3, timeout=10)
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator"""
        from app.circuit_breaker import circuit_breaker
        
        @circuit_breaker(failure_threshold=2, timeout=5)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
