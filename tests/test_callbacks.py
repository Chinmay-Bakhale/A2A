"""
Tests for security callbacks
"""

import pytest
from app.callbacks import (
    BeforeModelCallback, 
    AfterModelCallback,
    before_model_callback,
    after_model_callback
)


class TestBeforeModelCallback:
    """Test PII detection and content filtering"""
    
    def test_no_pii_detected(self):
        """Test clean message without PII"""
        messages = [
            {"role": "user", "content": "What is my leave balance?"}
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is True
        assert result["blocked"] is False
        assert len(result["pii_detected"]) == 0
        assert result["modified_messages"] == messages
    
    def test_email_detection_and_masking(self):
        """Test email PII detection and masking"""
        messages = [
            {"role": "user", "content": "My email is john.doe@example.com"}
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is True
        assert "email" in result["pii_detected"]
        assert "john.doe@example.com" not in result["modified_messages"][0]["content"]
        assert "[EMAIL_REDACTED]" in result["modified_messages"][0]["content"]
    
    def test_phone_detection_and_masking(self):
        """Test phone number PII detection"""
        messages = [
            {"role": "user", "content": "Call me at 123-456-7890"}
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is True
        assert "phone" in result["pii_detected"]
        assert "[PHONE_REDACTED]" in result["modified_messages"][0]["content"]
    
    def test_credit_card_detection_and_masking(self):
        """Test credit card PII detection"""
        messages = [
            {"role": "user", "content": "Card number: 4532-1234-5678-9010"}
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is True
        assert "credit_card" in result["pii_detected"]
        assert "[CREDIT_CARD_REDACTED]" in result["modified_messages"][0]["content"]
    
    def test_multiple_pii_types(self):
        """Test detection of multiple PII types"""
        messages = [
            {
                "role": "user",
                "content": "My email is john@example.com and phone is 123-456-7890"
            }
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is True
        assert "email" in result["pii_detected"]
        assert "phone" in result["pii_detected"]
    
    def test_blocked_content(self):
        """Test content blocking for unauthorized requests"""
        messages = [
            {"role": "user", "content": "Please hack into the database"}
        ]
        
        result = before_model_callback(messages)
        
        assert result["allowed"] is False
        assert result["blocked"] is True
        assert "blocked_reason" in result
    
    def test_stats_tracking(self):
        """Test callback statistics tracking"""
        # Reset stats
        before_model_callback.total_calls = 0
        
        messages = [{"role": "user", "content": "test"}]
        before_model_callback(messages)
        
        stats = before_model_callback.get_stats()
        
        assert stats["total_calls"] == 1
        assert "pii_detections" in stats
        assert "content_blocked" in stats


class TestAfterModelCallback:
    """Test response validation"""
    
    def test_valid_response(self):
        """Test valid response validation"""
        response = {
            "content": "Your leave balance is 10 days.",
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70
            }
        }
        
        result = after_model_callback(response)
        
        assert result["valid"] is True
        assert result["response"] == response
    
    def test_empty_content(self):
        """Test empty content validation"""
        response = {
            "content": "",
            "usage": {"total_tokens": 0}
        }
        
        result = after_model_callback(response)
        
        # Empty content is marked as invalid by the callback
        assert result["valid"] is False
    
    def test_missing_usage(self):
        """Test response with missing usage"""
        response = {
            "content": "Test response"
        }
        
        # Should still work, but usage will be default
        result = after_model_callback(response)
        
        assert result["valid"] is True
    
    def test_token_tracking(self):
        """Test token usage tracking"""
        # Reset stats
        after_model_callback.total_calls = 0
        after_model_callback.response_count = 0
        after_model_callback.total_tokens = 0
        
        response = {
            "content": "Test",
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70
            }
        }
        
        after_model_callback(response)
        
        stats = after_model_callback.get_stats()
        
        assert stats["total_calls"] == 1
        assert stats["total_tokens"] == 70
        assert stats["average_tokens"] == 70.0
    
    def test_average_token_calculation(self):
        """Test average token calculation"""
        # Reset stats
        after_model_callback.total_calls = 0
        after_model_callback.response_count = 0
        after_model_callback.total_tokens = 0
        
        # First response: 100 tokens
        after_model_callback({
            "content": "Test",
            "usage": {"total_tokens": 100}
        })
        
        # Second response: 200 tokens
        after_model_callback({
            "content": "Test",
            "usage": {"total_tokens": 200}
        })
        
        stats = after_model_callback.get_stats()
        
        assert stats["total_calls"] == 2
        assert stats["total_tokens"] == 300
        assert stats["average_tokens"] == 150.0
