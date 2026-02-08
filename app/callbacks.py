"""
Security callbacks for the ADK agent
- Before Model Callback: PII detection, content filtering
- After Model Callback: Response validation, logging
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Import metrics if available
try:
    from app.metrics import record_pii_detection, record_security_block
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


# PII patterns to detect and mask (India-relevant)
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US/India phone formats
    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "passport": r'\b[A-Z]{1,2}\d{6,9}\b'  # International passport format
}

# Blocked content patterns
BLOCKED_PATTERNS = [
    r'(?i)(hack|exploit|attack|malicious)',
    r'(?i)(password|secret|api[_\s]?key)',
    r'(?i)(sql\s+injection|xss|csrf)'
]


class BeforeModelCallback:
    """
    Callback executed BEFORE sending request to LLM
    Responsibilities:
    - Detect and mask PII
    - Filter blocked content
    - Log security events
    """
    
    def __init__(self):
        self.total_calls = 0
        self.pii_detected_count = 0
        self.blocked_content_count = 0
    
    def __call__(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Process messages before sending to LLM
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional context
            
        Returns:
            Dict with processed messages and metadata
        """
        logger.info("BeforeModelCallback: Processing messages")
        self.total_calls += 1
        
        processed_messages = []
        pii_detected = []
        blocked = False
        
        for message in messages:
            content = message.get("content", "")
            
            # Check for blocked content
            if self._contains_blocked_content(content):
                logger.warning(f"BeforeModelCallback: Blocked content detected")
                self.blocked_content_count += 1
                blocked = True
                break
            
            # Detect and mask PII
            masked_content, detected_pii = self._mask_pii(content)
            if detected_pii:
                pii_detected.extend(detected_pii)
                self.pii_detected_count += len(detected_pii)
            
            # Create processed message
            processed_message = message.copy()
            processed_message["content"] = masked_content
            processed_messages.append(processed_message)
        
        # Log security events and record metrics
        if pii_detected:
            logger.warning(f"BeforeModelCallback: PII detected and masked: {pii_detected}")
            if METRICS_AVAILABLE:
                for pii_type in pii_detected:
                    record_pii_detection(pii_type)
        
        if blocked and METRICS_AVAILABLE:
            record_security_block()
        
        result = {
            "allowed": not blocked,
            "blocked": blocked,
            "messages": processed_messages if not blocked else [],
            "pii_detected": pii_detected,
            "modified_messages": processed_messages if not blocked else [],
            "metadata": {
                "pii_detected": pii_detected,
                "pii_count": len(pii_detected),
                "blocked": blocked,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if blocked:
            result["error"] = "Content blocked due to security policy violation"
            result["blocked_reason"] = "Security policy violation detected"
        
        return result
    
    def _mask_pii(self, text: str) -> tuple[str, List[str]]:
        """
        Detect and mask PII in text
        
        Returns:
            Tuple of (masked_text, list_of_detected_pii_types)
        """
        masked_text = text
        detected = []
        
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                detected.append(pii_type)
                # Mask the PII
                masked_text = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", masked_text)
        
        return masked_text, detected
    
    def _contains_blocked_content(self, text: str) -> bool:
        """Check if text contains blocked patterns"""
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get callback statistics"""
        return {
            "total_calls": self.total_calls,
            "pii_detections": self.pii_detected_count,
            "content_blocked": self.blocked_content_count
        }


class AfterModelCallback:
    """
    Callback executed AFTER receiving response from LLM
    Responsibilities:
    - Validate response format
    - Log model interactions
    - Track metrics
    """
    
    def __init__(self):
        self.total_calls = 0
        self.response_count = 0
        self.error_count = 0
        self.total_tokens = 0
    
    def __call__(self, response: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Process response after LLM generation
        
        Args:
            response: LLM response dictionary
            **kwargs: Additional context
            
        Returns:
            Dict with processed response and metadata
        """
        logger.info("AfterModelCallback: Processing response")
        
        self.total_calls += 1
        self.response_count += 1
        
        # Extract response content
        content = response.get("content", "")
        
        # Validate response
        is_valid, validation_errors = self._validate_response(response)
        
        if not is_valid:
            logger.error(f"AfterModelCallback: Invalid response - {validation_errors}")
            self.error_count += 1
        
        # Track token usage
        token_usage = response.get("usage", {})
        tokens = token_usage.get("total_tokens", 0)
        self.total_tokens += tokens
        
        # Log interaction
        self._log_interaction(response, is_valid)
        
        return {
            "valid": is_valid,
            "response": response,
            "metadata": {
                "is_valid": is_valid,
                "validation_errors": validation_errors if not is_valid else None,
                "tokens_used": tokens,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _validate_response(self, response: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate response structure and content
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if response has content
        if not response.get("content"):
            errors.append("Response is missing content")
        
        # Check for error indicators in response
        if "error" in response:
            errors.append(f"Response contains error: {response['error']}")
        
        # Check response length (prevent extremely long responses)
        content = response.get("content", "")
        if len(content) > 10000:  # 10k character limit
            errors.append("Response exceeds maximum length")
        
        return len(errors) == 0, errors
    
    def _log_interaction(self, response: Dict[str, Any], is_valid: bool):
        """Log model interaction for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "is_valid": is_valid,
            "token_usage": response.get("usage", {}),
            "model": response.get("model", "unknown")
        }
        
        # In production, this would go to a proper logging service
        logger.info(f"Model interaction logged: {log_entry}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get callback statistics"""
        return {
            "total_calls": self.total_calls,
            "response_count": self.response_count,
            "error_count": self.error_count,
            "total_tokens": self.total_tokens,
            "average_tokens": self.total_tokens / max(self.response_count, 1)
        }


# Initialize global callbacks
before_model_callback = BeforeModelCallback()
after_model_callback = AfterModelCallback()
