from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable

REQUEST_COUNT = Counter(
    'leave_assistant_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

REQUEST_DURATION = Histogram(
    'leave_assistant_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

ACTIVE_REQUESTS = Gauge(
    'leave_assistant_active_requests',
    'Number of active requests'
)

AGENT_RESPONSES = Counter(
    'leave_assistant_agent_responses_total',
    'Total number of agent responses',
    ['status']
)

TOOL_CALLS = Counter(
    'leave_assistant_tool_calls_total',
    'Total number of tool calls',
    ['tool_name', 'status']
)

PII_DETECTIONS = Counter(
    'leave_assistant_pii_detections_total',
    'Total PII detections',
    ['pii_type']
)

SECURITY_BLOCKS = Counter(
    'leave_assistant_security_blocks_total',
    'Total security content blocks'
)

CIRCUIT_BREAKER_STATE = Gauge(
    'leave_assistant_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)

TOKEN_USAGE = Counter(
    'leave_assistant_tokens_total',
    'Total tokens used',
    ['type']
)

RESPONSE_TIME = Histogram(
    'leave_assistant_llm_response_seconds',
    'LLM response time in seconds'
)


def track_request(endpoint: str, method: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ACTIVE_REQUESTS.inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = 'success'
                REQUEST_COUNT.labels(
                    endpoint=endpoint,
                    method=method,
                    status=status
                ).inc()
                return result
                
            except Exception as e:
                status = 'error'
                REQUEST_COUNT.labels(
                    endpoint=endpoint,
                    method=method,
                    status=status
                ).inc()
                raise
                
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(
                    endpoint=endpoint,
                    method=method
                ).observe(duration)
                ACTIVE_REQUESTS.dec()
        
        return wrapper
    return decorator


def record_agent_response(success: bool):
    status = 'success' if success else 'error'
    AGENT_RESPONSES.labels(status=status).inc()


def record_tool_call(tool_name: str, success: bool):
    status = 'success' if success else 'error'
    TOOL_CALLS.labels(tool_name=tool_name, status=status).inc()


def record_pii_detection(pii_type: str = "unknown"):
    PII_DETECTIONS.labels(pii_type=pii_type).inc()


def record_security_block():
    SECURITY_BLOCKS.inc()


def record_circuit_breaker_state(service: str, state: str):
    state_map = {'closed': 0, 'open': 1, 'half_open': 2}
    CIRCUIT_BREAKER_STATE.labels(service=service).set(state_map.get(state, 0))


def record_token_usage(prompt_tokens: int, completion_tokens: int, total_tokens: int):
    TOKEN_USAGE.labels(type='prompt').inc(prompt_tokens)
    TOKEN_USAGE.labels(type='completion').inc(completion_tokens)
    TOKEN_USAGE.labels(type='total').inc(total_tokens)


def record_llm_response_time(duration: float):
    RESPONSE_TIME.observe(duration)


def get_metrics() -> tuple[str, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
