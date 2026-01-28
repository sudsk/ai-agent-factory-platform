"""
Guardrails Module

Provides decorators and utilities for input/output validation and safety.
"""

import re
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional
from google.cloud import dlp_v2

logger = logging.getLogger(__name__)


class Guardrails:
    """Decorator-based guardrails for agents"""
    
    _dlp_client = None
    _project_id = None
    
    @classmethod
    def init(cls, project_id: str):
        """Initialize guardrails with GCP project"""
        cls._project_id = project_id
        cls._dlp_client = dlp_v2.DlpServiceClient()
    
    @staticmethod
    def validate_input(
        check_prompt_injection: bool = True,
        check_pii: bool = True,
        redact_pii: bool = False,
        max_length: Optional[int] = None,
    ):
        """
        Validate input before agent processing
        
        Args:
            check_prompt_injection: Check for prompt injection attempts
            check_pii: Check for PII in input
            redact_pii: Automatically redact PII if found
            max_length: Maximum input length in characters
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract input data
                if len(args) > 1:
                    input_data = args[1]
                else:
                    input_data = kwargs.get('input_data') or kwargs.get('request')
                
                if not input_data:
                    logger.warning("No input data found to validate")
                    return func(*args, **kwargs)
                
                # Convert to string for validation
                input_str = str(input_data)
                
                # Check length
                if max_length and len(input_str) > max_length:
                    raise ValueError(f"Input exceeds maximum length of {max_length} characters")
                
                # Check for prompt injection
                if check_prompt_injection and Guardrails._has_prompt_injection(input_str):
                    logger.warning("Potential prompt injection detected")
                    raise ValueError("Potential prompt injection detected in input")
                
                # Check for PII
                if check_pii:
                    pii_findings = Guardrails._detect_pii(input_str)
                    if pii_findings:
                        if redact_pii:
                            logger.info(f"PII detected and will be redacted: {len(pii_findings)} findings")
                            input_data = Guardrails._redact_pii_gcp(input_data)
                            # Update args/kwargs with redacted data
                            if len(args) > 1:
                                args = (args[0], input_data) + args[2:]
                            else:
                                if 'input_data' in kwargs:
                                    kwargs['input_data'] = input_data
                                elif 'request' in kwargs:
                                    kwargs['request'] = input_data
                        else:
                            logger.warning(f"PII detected in input: {len(pii_findings)} findings")
                            raise ValueError(f"PII detected in input: {[f['info_type'] for f in pii_findings]}")
                
                logger.info("Input validation passed")
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def validate_output(
        check_toxicity: bool = True,
        check_pii: bool = True,
        redact_pii: bool = True,
        max_length: Optional[int] = None,
    ):
        """
        Validate output after agent processing
        
        Args:
            check_toxicity: Check for toxic content
            check_pii: Check for PII in output
            redact_pii: Automatically redact PII if found
            max_length: Maximum output length in characters
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                if not result:
                    return result
                
                # Convert to string for validation
                result_str = str(result)
                
                # Check length
                if max_length and len(result_str) > max_length:
                    logger.warning(f"Output exceeds maximum length: {len(result_str)} > {max_length}")
                    # Truncate or raise based on preference
                    raise ValueError(f"Output exceeds maximum length of {max_length} characters")
                
                # Check for toxicity
                if check_toxicity and Guardrails._is_toxic(result_str):
                    logger.error("Toxic content detected in output")
                    raise ValueError("Toxic content detected in agent output")
                
                # Check for PII in output
                if check_pii:
                    pii_findings = Guardrails._detect_pii(result_str)
                    if pii_findings:
                        if redact_pii:
                            logger.warning(f"PII detected in output and will be redacted: {len(pii_findings)} findings")
                            result = Guardrails._redact_pii_gcp(result)
                        else:
                            logger.error(f"PII detected in output: {len(pii_findings)} findings")
                            raise ValueError(f"PII detected in output: {[f['info_type'] for f in pii_findings]}")
                
                # Log output metrics
                Guardrails._log_output_metrics(result)
                
                logger.info("Output validation passed")
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def _has_prompt_injection(text: str) -> bool:
        """
        Simple prompt injection detection
        
        Args:
            text: Text to check
            
        Returns:
            True if potential prompt injection detected
        """
        patterns = [
            r"ignore\s+(previous|above|all|prior)\s+instructions",
            r"system\s+prompt",
            r"you\s+are\s+now",
            r"<\|im_start\|>",
            r"<\|im_end\|>",
            r"disregard\s+(previous|above|all|prior)",
            r"forget\s+(everything|all|previous)",
            r"new\s+instructions?:",
            r"admin\s+mode",
            r"developer\s+mode",
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def _detect_pii(text: str) -> list:
        """
        Detect PII using simple regex patterns
        
        Args:
            text: Text to check
            
        Returns:
            List of PII findings
        """
        findings = []
        
        # SSN pattern
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            findings.append({"info_type": "SSN", "likelihood": "LIKELY"})
        
        # Credit card pattern
        if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', text):
            findings.append({"info_type": "CREDIT_CARD", "likelihood": "LIKELY"})
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            findings.append({"info_type": "EMAIL_ADDRESS", "likelihood": "LIKELY"})
        
        # Phone pattern (US)
        if re.search(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
            findings.append({"info_type": "PHONE_NUMBER", "likelihood": "POSSIBLE"})
        
        return findings
    
    @staticmethod
    def _redact_pii_gcp(data: Any) -> Any:
        """
        Redact PII using Google Cloud DLP API
        
        Args:
            data: Data to redact (dict or string)
            
        Returns:
            Redacted data
        """
        if not Guardrails._dlp_client or not Guardrails._project_id:
            logger.warning("DLP client not initialized, using regex-based redaction")
            return Guardrails._redact_pii_regex(data)
        
        try:
            # Convert data to string
            if isinstance(data, dict):
                import json
                text = json.dumps(data)
            else:
                text = str(data)
            
            # Configure DLP request
            inspect_config = {
                "info_types": [
                    {"name": "EMAIL_ADDRESS"},
                    {"name": "PHONE_NUMBER"},
                    {"name": "CREDIT_CARD_NUMBER"},
                    {"name": "US_SOCIAL_SECURITY_NUMBER"},
                    {"name": "PERSON_NAME"},
                ],
            }
            
            deidentify_config = {
                "info_type_transformations": {
                    "transformations": [
                        {
                            "primitive_transformation": {
                                "replace_with_info_type_config": {}
                            }
                        }
                    ]
                }
            }
            
            item = {"value": text}
            
            parent = f"projects/{Guardrails._project_id}"
            
            response = Guardrails._dlp_client.deidentify_content(
                request={
                    "parent": parent,
                    "deidentify_config": deidentify_config,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )
            
            redacted_text = response.item.value
            
            # Convert back to original type
            if isinstance(data, dict):
                import json
                return json.loads(redacted_text)
            return redacted_text
            
        except Exception as e:
            logger.error(f"DLP redaction failed: {e}, falling back to regex")
            return Guardrails._redact_pii_regex(data)
    
    @staticmethod
    def _redact_pii_regex(data: Any) -> Any:
        """
        Redact PII using regex (fallback method)
        
        Args:
            data: Data to redact
            
        Returns:
            Redacted data
        """
        if isinstance(data, dict):
            import json
            text = json.dumps(data)
        else:
            text = str(data)
        
        # Redact SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', text)
        
        # Redact credit cards
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD_REDACTED]', text)
        
        # Redact emails
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            text
        )
        
        # Redact phone numbers
        text = re.sub(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]', text)
        
        if isinstance(data, dict):
            import json
            return json.loads(text)
        return text
    
    @staticmethod
    def _is_toxic(text: str) -> bool:
        """
        Check for toxic content using simple keyword matching
        
        In production, use Perspective API or similar service
        
        Args:
            text: Text to check
            
        Returns:
            True if toxic content detected
        """
        # This is a placeholder - integrate with Perspective API in production
        toxic_keywords = [
            "hate", "kill", "threat", "violence", "terrorist",
            # Add more based on your use case
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in toxic_keywords)
    
    @staticmethod
    def _log_output_metrics(data: Any):
        """
        Log output metrics for monitoring
        
        Args:
            data: Output data to log metrics for
        """
        try:
            from google.cloud import monitoring_v3
            import time
            
            # Log output size
            output_size = len(str(data))
            
            logger.debug(f"Output size: {output_size} characters")
            
            # In production, send custom metrics to Cloud Monitoring
            # client = monitoring_v3.MetricServiceClient()
            # ... send metrics
            
        except Exception as e:
            logger.debug(f"Failed to log output metrics: {e}")


class RateLimiter:
    """Simple rate limiter for agent invocations"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests = {}
    
    def check_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (user ID, API key, etc.)
            
        Returns:
            True if within limit, False otherwise
        """
        import time
        
        now = time.time()
        
        # Clean old entries
        if identifier in self._requests:
            self._requests[identifier] = [
                ts for ts in self._requests[identifier]
                if now - ts < self.time_window
            ]
        else:
            self._requests[identifier] = []
        
        # Check limit
        if len(self._requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self._requests[identifier].append(now)
        return True
    
    def __call__(self, identifier_func: Callable):
        """Decorator for rate limiting"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get identifier
                identifier = identifier_func(*args, **kwargs)
                
                if not self.check_limit(identifier):
                    raise ValueError(f"Rate limit exceeded for {identifier}")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
