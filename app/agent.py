import logging
import time
from typing import List, Dict, Any, Optional
from litellm import completion
from app.tools import AGENT_TOOLS
from app.callbacks import before_model_callback, after_model_callback

logger = logging.getLogger(__name__)

try:
    from app.metrics import record_token_usage, record_llm_response_time, record_tool_call
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


SYSTEM_INSTRUCTIONS = """You are a Leave Policy Assistant for a multinational company.

Help employees with:
- Leave policies (PTO, Sick Leave,Parental Leave, etc.)
- Leave balances
- Eligibility checks
- Policy explanations

Guidelines:
- Be professional and helpful
- Ask for employee ID if needed
- Verify balance, notice period, max consecutive days, and blackout periods
- Explain rules simply
- Mention if manager approval is required

Use your tools to check balances, calculate eligibility, and get policy details.
Always validate dates are in YYYY-MM-DD format.
"""


class LeaveAssistantAgent:
    def __init__(self, model: str = "gemini/gemini-pro", temperature: float = 0.7, max_tokens: int = 1000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.before_callback = before_model_callback
        self.after_callback = after_model_callback
    
    def chat(self, message: str, session_id: str, employee_id: Optional[str] = None) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS}
            ]
        
        context = f"\n[Context: Employee ID is {employee_id}]" if employee_id else ""
        user_message = {"role": "user", "content": message + context}
        self.sessions[session_id].append(user_message)
        
        callback_result = self.before_callback(self.sessions[session_id])
        
        if callback_result.get("blocked", False):
            return {
                "response": "I'm sorry, but I cannot process that request due to security policies.",
                "session_id": session_id,
                "error": callback_result.get("error"),
                "blocked": True
            }
        
        messages = callback_result["messages"]
        response = self._generate_response(messages)
        after_result = self.after_callback(response)
        response_content = response.get("content", "")
        
        self.sessions[session_id].append({
            "role": "assistant",
            "content": response_content
        })
        
        return {
            "response": response_content,
            "session_id": session_id,
            "metadata": {
                "before_callback": callback_result.get("metadata"),
                "after_callback": after_result.get("metadata"),
                "model": self.model
            }
        }
    
    def _generate_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in AGENT_TOOLS
        ]
        
        from litellm.exceptions import RateLimitError
        
        for attempt in range(3):
            try:
                start_time = time.time()
                response = completion(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    tools=tools,
                    tool_choice="auto"
                )
                
                if METRICS_AVAILABLE:
                    record_llm_response_time(time.time() - start_time)
                
                break
                
            except RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** attempt * 2)
                else:
                    raise
        
        message = response.choices[0].message
        
        usage_dict = {}
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
            completion_tokens = getattr(response.usage, 'completion_tokens', 0)
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            
            usage_dict = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            
            if METRICS_AVAILABLE:
                record_token_usage(prompt_tokens, completion_tokens, total_tokens)
        
        return {
            "content": message.content,
            "usage": usage_dict,
            "model": self.model
        }
    
    def _handle_tool_calls(self, messages: List[Dict[str, Any]], assistant_message: Any, original_response: Any) -> Dict[str, Any]:
        import json
        
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })
        
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            tool_function = next((tool["function"] for tool in AGENT_TOOLS if tool["name"] == function_name), None)
            
            if tool_function:
                result = tool_function(**function_args)
                result_str = json.dumps(result)
                if METRICS_AVAILABLE:
                    record_tool_call(function_name, success=True)
            else:
                result_str = json.dumps({"error": f"Tool {function_name} not found"})
                if METRICS_AVAILABLE:
                    record_tool_call(function_name, success=False)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })
        
        final_response = completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        final_message = final_response.choices[0].message
        
        usage_dict = {}
        if hasattr(final_response, 'usage') and final_response.usage:
            usage_dict = {
                "prompt_tokens": getattr(final_response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(final_response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(final_response.usage, 'total_tokens', 0)
            }
        
        return {
            "content": final_message.content,
            "usage": usage_dict,
            "model": self.model,
            "tool_calls_executed": len(assistant_message.tool_calls)
        }
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self.sessions.get(session_id, [])


_agent: Optional[LeaveAssistantAgent] = None


def get_agent() -> LeaveAssistantAgent:
    global _agent
    if _agent is None:
        import os
        model = os.getenv("LITELLM_MODEL", "gemini/gemini-pro")
        _agent = LeaveAssistantAgent(model=model)
    return _agent
