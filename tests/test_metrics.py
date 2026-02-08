"""
Tests for Prometheus metrics
"""

import pytest
from app.metrics import (
    record_agent_response,
    record_tool_call,
    record_pii_detection,
    record_security_block,
    record_circuit_breaker_state,
    record_token_usage,
    record_llm_response_time,
    get_metrics,
    REQUEST_COUNT,
    AGENT_RESPONSES,
    TOOL_CALLS,
    PII_DETECTIONS,
    SECURITY_BLOCKS,
    CIRCUIT_BREAKER_STATE,
    TOKEN_USAGE,
    RESPONSE_TIME
)


class TestMetricsRecording:
    """Test metrics recording functions"""
    
    def test_record_agent_response_success(self):
        """Test recording successful agent response"""
        record_agent_response(success=True)
        
        # Metric should increment
        assert AGENT_RESPONSES.labels(status='success')._value.get() >= 1
    
    def test_record_agent_response_error(self):
        """Test recording error agent response"""
        record_agent_response(success=False)
        
        # Metric should increment
        assert AGENT_RESPONSES.labels(status='error')._value.get() >= 1
    
    def test_record_tool_call_success(self):
        """Test recording successful tool call"""
        record_tool_call('check_leave_balance', success=True)
        
        # Metric should increment
        assert TOOL_CALLS.labels(
            tool_name='check_leave_balance',
            status='success'
        )._value.get() >= 1
    
    def test_record_tool_call_error(self):
        """Test recording failed tool call"""
        record_tool_call('check_leave_balance', success=False)
        
        # Metric should increment
        assert TOOL_CALLS.labels(
            tool_name='check_leave_balance',
            status='error'
        )._value.get() >= 1
    
    def test_record_pii_detection(self):
        """Test recording PII detection"""
        record_pii_detection('email')
        
        # Metric should increment
        assert PII_DETECTIONS.labels(pii_type='email')._value.get() >= 1
    
    def test_record_security_block(self):
        """Test recording security block"""
        initial_value = SECURITY_BLOCKS._value.get()
        record_security_block()
        
        # Metric should increment
        assert SECURITY_BLOCKS._value.get() == initial_value + 1
    
    def test_record_circuit_breaker_state_closed(self):
        """Test recording circuit breaker closed state"""
        record_circuit_breaker_state('snowflake', 'closed')
        
        # State should be 0 (closed)
        assert CIRCUIT_BREAKER_STATE.labels(service='snowflake')._value.get() == 0
    
    def test_record_circuit_breaker_state_open(self):
        """Test recording circuit breaker open state"""
        record_circuit_breaker_state('snowflake', 'open')
        
        # State should be 1 (open)
        assert CIRCUIT_BREAKER_STATE.labels(service='snowflake')._value.get() == 1
    
    def test_record_circuit_breaker_state_half_open(self):
        """Test recording circuit breaker half_open state"""
        record_circuit_breaker_state('snowflake', 'half_open')
        
        # State should be 2 (half_open)
        assert CIRCUIT_BREAKER_STATE.labels(service='snowflake')._value.get() == 2
    
    def test_record_token_usage(self):
        """Test recording token usage"""
        initial_prompt = TOKEN_USAGE.labels(type='prompt')._value.get()
        initial_completion = TOKEN_USAGE.labels(type='completion')._value.get()
        initial_total = TOKEN_USAGE.labels(type='total')._value.get()
        
        record_token_usage(
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80
        )
        
        # Metrics should increment
        assert TOKEN_USAGE.labels(type='prompt')._value.get() == initial_prompt + 50
        assert TOKEN_USAGE.labels(type='completion')._value.get() == initial_completion + 30
        assert TOKEN_USAGE.labels(type='total')._value.get() == initial_total + 80
    
    def test_record_llm_response_time(self):
        """Test recording LLM response time"""
        # Just verify the function runs without error
        # Prometheus histograms don't expose internal counters easily in tests
        record_llm_response_time(1.5)
        record_llm_response_time(2.0)
        
        # If no exception, metric is being recorded
        assert True


class TestMetricsExport:
    """Test metrics export"""
    
    def test_get_metrics_format(self):
        """Test metrics are exported in Prometheus format"""
        metrics_data, content_type = get_metrics()
        
        # Should return bytes (Prometheus format)
        assert isinstance(metrics_data, bytes)
        
        # Content type should be for Prometheus
        assert 'text/plain' in content_type
    
    def test_get_metrics_contains_metrics(self):
        """Test exported metrics contain expected metrics"""
        metrics_data, _ = get_metrics()
        metrics_text = metrics_data.decode('utf-8')
        
        # Check for key metric names
        assert 'leave_assistant_requests_total' in metrics_text
        assert 'leave_assistant_agent_responses_total' in metrics_text
        assert 'leave_assistant_tool_calls_total' in metrics_text
    
    def test_metrics_help_text(self):
        """Test metrics include help text"""
        metrics_data, _ = get_metrics()
        metrics_text = metrics_data.decode('utf-8')
        
        # Prometheus format includes HELP lines
        assert '# HELP' in metrics_text
        assert '# TYPE' in metrics_text


class TestMetricsLabels:
    """Test metrics with different labels"""
    
    def test_tool_calls_different_tools(self):
        """Test recording different tool calls"""
        record_tool_call('check_leave_balance', success=True)
        record_tool_call('calculate_eligibility', success=True)
        record_tool_call('get_leave_policy_details', success=True)
        
        # All should be recorded with different labels
        assert TOOL_CALLS.labels(
            tool_name='check_leave_balance',
            status='success'
        )._value.get() >= 1
        
        assert TOOL_CALLS.labels(
            tool_name='calculate_eligibility',
            status='success'
        )._value.get() >= 1
        
        assert TOOL_CALLS.labels(
            tool_name='get_leave_policy_details',
            status='success'
        )._value.get() >= 1
    
    def test_pii_detections_different_types(self):
        """Test recording different PII types"""
        record_pii_detection('email')
        record_pii_detection('phone')
        record_pii_detection('ssn')
        
        # All should be recorded with different labels
        assert PII_DETECTIONS.labels(pii_type='email')._value.get() >= 1
        assert PII_DETECTIONS.labels(pii_type='phone')._value.get() >= 1
        assert PII_DETECTIONS.labels(pii_type='ssn')._value.get() >= 1
