"""
Core Leave Policy Assistant Agent using Google ADK
"""

import logging
from typing import List, Dict, Any, Optional
from google.adk.agents import Agent
from litellm import completion
from app.tools import AGENT_TOOLS, check_leave_balance, calculate_eligibility, get_leave_policy_details
from app.callbacks import before_model_callback, after_model_callback

logger = logging.getLogger(__name__)


# Agent system instructions
SYSTEM_INSTRUCTIONS = """You are a helpful Leave Policy Assistant for a multinational company.

Your role is to:
1. Answer employee questions about leave policies (PTO, Sick Leave, Parental Leave, etc.)
2. Check employee leave balances
3. Determine if employees are eligible for requested leave
4. Explain policy rules clearly and concisely

Guidelines:
- Be friendly, professional, and helpful
- If you need an employee ID to answer a question, politely ask for it
- When checking eligibility, always verify: balance, notice period, maximum consecutive days, and blackout periods
- Explain policy rules in simple terms
- If information is missing or unclear, ask clarifying questions
- Always mention if manager approval is required

Available information:
- Leave policies for US, India, and UK
- Employee leave balances and information
- Policy rules (allowances, carryover limits, notice requirements, etc.)

Use your tools to:
- check_leave_balance: Get current leave balance for an employee
- calculate_eligibility: Check if an employee can take specific leave
- get_leave_policy_details: Get policy information for a country/leave type

Remember:
- Always validate dates are in YYYY-MM-DD format
- Be helpful even when denying requests - explain why and suggest alternatives
- Respect employee privacy and data security
"""


class LeaveAssistantAgent:
    """
    Leave Policy Assistant Agent using Google ADK and LiteLLM
    """
    
    def __init__(
        self,
        model: str = "gemini/gemini-pro",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize the Leave Assistant Agent
        
        Args:
            model: LiteLLM model identifier
            temperature: Model temperature for response generation
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Conversation history per session
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize callbacks
        self.before_callback = before_model_callback
        self.after_callback = after_model_callback
        
        logger.info(f"LeaveAssistantAgent initialized with model: {model}")
    
    def chat(
        self,
        message: str,
        session_id: str,
        employee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response
        
        Args:
            message: User's message
            session_id: Session ID for conversation continuity
            employee_id: Optional employee ID for context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            logger.info(f"Processing message for session {session_id}")
            
            # Initialize session if new
            if session_id not in self.sessions:
                self.sessions[session_id] = [
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS}
                ]
            
            # Add employee context if provided
            context = ""
            if employee_id:
                context = f"\n[Context: Employee ID is {employee_id}]"
            
            # Add user message to history
            user_message = {"role": "user", "content": message + context}
            self.sessions[session_id].append(user_message)
            
            # Apply before model callback
            callback_result = self.before_callback(self.sessions[session_id])
            
            # Check if content was blocked
            if callback_result.get("metadata", {}).get("blocked"):
                return {
                    "response": "I'm sorry, but I cannot process that request due to security policies.",
                    "session_id": session_id,
                    "error": callback_result.get("error"),
                    "blocked": True
                }
            
            # Get processed messages
            messages = callback_result["messages"]
            
            # Check if we need to call tools
            response = self._generate_response(messages)
            
            # Apply after model callback
            after_result = self.after_callback(response)
            
            # Extract response content
            response_content = response.get("content", "")
            
            # Add assistant response to history
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
            
        except Exception as e:
            logger.error(f"Error processing chat: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "session_id": session_id,
                "error": str(e)
            }
    
    def _generate_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate response using LiteLLM with function calling
        
        Args:
            messages: Conversation history
            
        Returns:
            Response dictionary
        """
        try:
            # Define tools for function calling
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
            
            # Call LiteLLM with tools and retry logic
            import time
            from litellm.exceptions import RateLimitError
            
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = completion(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        tools=tools,
                        tool_choice="auto"
                    )
                    break  # Success, exit retry loop
                    
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        # Last attempt failed, re-raise
                        raise
            
            
            message = response.choices[0].message
            
            # Check if model wants to call a tool
            if hasattr(message, 'tool_calls') and message.tool_calls:
                return self._handle_tool_calls(messages, message, response)
            
            # No tool call, return response
            usage_dict = {}
            if hasattr(response, 'usage') and response.usage:
                # Convert usage object to dict
                usage_dict = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            
            return {
                "content": message.content,
                "usage": usage_dict,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "content": "I apologize, but I'm having trouble generating a response right now.",
                "error": str(e)
            }
    
    def _handle_tool_calls(
        self,
        messages: List[Dict[str, Any]],
        assistant_message: Any,
        original_response: Any
    ) -> Dict[str, Any]:
        """
        Handle tool/function calls from the model
        
        Args:
            messages: Conversation history
            assistant_message: Message with tool calls
            original_response: Original LiteLLM response
            
        Returns:
            Final response after tool execution
        """
        import json
        
        # Add assistant message with tool calls to conversation
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
        
        # Execute each tool call
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Calling tool: {function_name} with args: {function_args}")
            
            # Find and execute the tool
            tool_function = None
            for tool in AGENT_TOOLS:
                if tool["name"] == function_name:
                    tool_function = tool["function"]
                    break
            
            if tool_function:
                try:
                    result = tool_function(**function_args)
                    result_str = json.dumps(result)
                except Exception as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    result_str = json.dumps({"error": str(e)})
            else:
                result_str = json.dumps({"error": f"Tool {function_name} not found"})
            
            # Add tool response to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })
        
        # Get final response from model with tool results
        final_response = completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        final_message = final_response.choices[0].message
        
        # Convert usage object to dict
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
        """Clear conversation history for a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} cleared")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.sessions.get(session_id, [])


# Global agent instance
_agent: Optional[LeaveAssistantAgent] = None


def get_agent() -> LeaveAssistantAgent:
    """
    Get or create the global agent instance
    
    Returns:
        LeaveAssistantAgent instance
    """
    global _agent
    
    if _agent is None:
        import os
        model = os.getenv("LITELLM_MODEL", "gemini/gemini-pro")
        _agent = LeaveAssistantAgent(model=model)
    
    return _agent
