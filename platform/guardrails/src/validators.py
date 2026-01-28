# platform/guardrails/src/validators.py

from functools import wraps
from typing import Callable
import re

class Guardrails:
    """Decorator-based guardrails for agents"""
    
    @staticmethod
    def validate_input():
        """Validate input before agent processing"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get input data
                input_data = args[1] if len(args) > 1 else kwargs.get('input_data')
                
                # Check for prompt injection
                if Guardrails._has_prompt_injection(input_data):
                    raise ValueError("Potential prompt injection detected")
                
                # Check for PII
                if Guardrails._contains_pii(input_data):
                    # Redact PII
                    input_data = Guardrails._redact_pii(input_data)
                
                # Continue with validated input
                if len(args) > 1:
                    args = (args[0], input_data) + args[2:]
                else:
                    kwargs['input_data'] = input_data
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def validate_output():
        """Validate output after agent processing"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                # Check for toxicity
                if Guardrails._is_toxic(result):
                    raise ValueError("Toxic content detected in output")
                
                # Log for monitoring
                Guardrails._log_output(result)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def _has_prompt_injection(data: dict) -> bool:
        """Simple prompt injection detection"""
        text = str(data)
        patterns = [
            r"ignore (previous|above) instructions",
            r"system prompt",
            r"you are now",
            r"<\|im_start\|>",
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def _contains_pii(data: dict) -> bool:
        """Check for PII patterns"""
        text = str(data)
        # SSN pattern
        if re.search(r'\d{3}-\d{2}-\d{4}', text):
            return True
        # Credit card pattern
        if re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', text):
            return True
        return False
    
    @staticmethod
    def _redact_pii(data: dict) -> dict:
        """Redact PII from data"""
        # Use Google DLP API for production
        from google.cloud import dlp_v2
        
        dlp = dlp_v2.DlpServiceClient()
        # Implement redaction logic
        return data
    
    @staticmethod
    def _is_toxic(data: dict) -> bool:
        """Check for toxic content"""
        # Use Perspective API or similar
        return False
    
    @staticmethod
    def _log_output(data: dict):
        """Log output for monitoring"""
        # Send to Cloud Logging
        pass