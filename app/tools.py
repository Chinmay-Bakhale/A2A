"""
Custom tools for the Leave Policy Assistant Agent
These tools will be called by the ADK agent to perform specific tasks
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.mock_data import (
    get_employee_by_id,
    get_employee_by_email,
    get_leave_policy,
    get_all_leave_types,
    LEAVE_POLICIES
)

logger = logging.getLogger(__name__)


def check_leave_balance(employee_id: str, leave_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the leave balance for an employee.
    
    Args:
        employee_id: Employee ID (e.g., 'EMP001')
        leave_type: Specific leave type to check (optional)
        
    Returns:
        Dictionary containing leave balance information
    """
    try:
        logger.info(f"Checking leave balance for employee: {employee_id}")
        
        # Get employee data
        employee = get_employee_by_id(employee_id)
        if not employee:
            return {
                "success": False,
                "error": f"Employee {employee_id} not found",
                "employee_id": employee_id
            }
        
        # If specific leave type requested
        if leave_type:
            balance = employee["leave_balances"].get(leave_type)
            if not balance:
                available_types = list(employee["leave_balances"].keys())
                return {
                    "success": False,
                    "error": f"Leave type '{leave_type}' not available for this employee",
                    "available_types": available_types,
                    "employee_id": employee_id
                }
            
            return {
                "success": True,
                "employee_id": employee_id,
                "employee_name": employee["name"],
                "country": employee["country"],
                "leave_type": leave_type,
                "balance": balance
            }
        
        # Return all leave balances
        return {
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "country": employee["country"],
            "all_balances": employee["leave_balances"]
        }
        
    except Exception as e:
        logger.error(f"Error checking leave balance: {str(e)}")
        return {
            "success": False,
            "error": f"Error retrieving leave balance: {str(e)}",
            "employee_id": employee_id
        }


def calculate_eligibility(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    num_days: int
) -> Dict[str, Any]:
    """
    Calculate if an employee is eligible to take leave based on:
    - Leave balance availability
    - Policy constraints (min notice, max consecutive days, blackout periods)
    - Pending requests
    
    Args:
        employee_id: Employee ID
        leave_type: Type of leave requested
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        num_days: Number of days requested
        
    Returns:
        Dictionary with eligibility status and details
    """
    try:
        logger.info(f"Calculating eligibility for {employee_id}: {leave_type}, {num_days} days")
        
        # Get employee data
        employee = get_employee_by_id(employee_id)
        if not employee:
            return {
                "eligible": False,
                "reason": f"Employee {employee_id} not found"
            }
        
        # Check if leave type exists for employee
        balance_info = employee["leave_balances"].get(leave_type)
        if not balance_info:
            available_types = list(employee["leave_balances"].keys())
            return {
                "eligible": False,
                "reason": f"Leave type '{leave_type}' not available",
                "available_types": available_types
            }
        
        # Get leave policy
        policy = get_leave_policy(employee["country"], leave_type)
        if not policy:
            return {
                "eligible": False,
                "reason": f"No policy found for {leave_type} in {employee['country']}"
            }
        
        # Check 1: Sufficient balance
        remaining = balance_info["remaining"]
        if num_days > remaining:
            return {
                "eligible": False,
                "reason": f"Insufficient balance. Requested: {num_days} days, Available: {remaining} days",
                "remaining_balance": remaining,
                "requested_days": num_days
            }
        
        # Check 2: Minimum notice period
        if "min_notice_days" in policy:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                today = datetime.now()
                notice_days = (start - today).days
                
                if notice_days < policy["min_notice_days"]:
                    return {
                        "eligible": False,
                        "reason": f"Minimum notice period not met. Required: {policy['min_notice_days']} days, Provided: {notice_days} days",
                        "min_notice_required": policy["min_notice_days"],
                        "notice_provided": notice_days
                    }
            except ValueError:
                return {
                    "eligible": False,
                    "reason": f"Invalid date format. Use YYYY-MM-DD"
                }
        
        # Check 3: Maximum consecutive days
        if "max_consecutive_days" in policy:
            if num_days > policy["max_consecutive_days"]:
                return {
                    "eligible": False,
                    "reason": f"Exceeds maximum consecutive days. Maximum: {policy['max_consecutive_days']} days, Requested: {num_days} days",
                    "max_allowed": policy["max_consecutive_days"],
                    "requested": num_days
                }
        
        # Check 4: Blackout periods
        if "blackout_periods" in policy:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                
                for blackout in policy["blackout_periods"]:
                    # Simple check - in production, parse actual date ranges
                    if blackout in f"{start_date} to {end_date}":
                        return {
                            "eligible": False,
                            "reason": f"Requested dates fall in blackout period: {blackout}",
                            "blackout_period": blackout
                        }
            except ValueError:
                pass
        
        # Check 5: Approval required
        approval_note = ""
        if policy.get("approval_required"):
            approval_note = "Manager approval required before confirmation"
        
        # All checks passed
        return {
            "eligible": True,
            "reason": "All eligibility criteria met",
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "leave_type": leave_type,
            "requested_days": num_days,
            "remaining_after": remaining - num_days,
            "policy_details": {
                "min_notice_days": policy.get("min_notice_days"),
                "max_consecutive_days": policy.get("max_consecutive_days"),
                "approval_required": policy.get("approval_required", False)
            },
            "additional_notes": approval_note if approval_note else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating eligibility: {str(e)}")
        return {
            "eligible": False,
            "reason": f"Error calculating eligibility: {str(e)}"
        }


def get_leave_policy_details(country: str, leave_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get leave policy details for a country and leave type.
    
    Args:
        country: Country code (e.g., 'US', 'India')
        leave_type: Specific leave type (optional)
        
    Returns:
        Dictionary with policy details
    """
    try:
        logger.info(f"Getting policy details for {country}, {leave_type}")
        
        if country not in LEAVE_POLICIES:
            available = list(LEAVE_POLICIES.keys())
            return {
                "success": False,
                "error": f"Country '{country}' not found",
                "available_countries": available
            }
        
        if leave_type:
            policy = get_leave_policy(country, leave_type)
            if not policy:
                available_types = get_all_leave_types(country)
                return {
                    "success": False,
                    "error": f"Leave type '{leave_type}' not found for {country}",
                    "available_types": available_types
                }
            
            return {
                "success": True,
                "country": country,
                "leave_type": leave_type,
                "policy": policy
            }
        
        # Return all policies for the country
        return {
            "success": True,
            "country": country,
            "all_policies": LEAVE_POLICIES[country]
        }
        
    except Exception as e:
        logger.error(f"Error getting policy details: {str(e)}")
        return {
            "success": False,
            "error": f"Error retrieving policy: {str(e)}"
        }


# Tool definitions for ADK agent
AGENT_TOOLS = [
    {
        "name": "check_leave_balance",
        "description": "Check the leave balance for an employee. Use this when the user asks about remaining leave days or leave balance.",
        "function": check_leave_balance,
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (e.g., EMP001)"
                },
                "leave_type": {
                    "type": "string",
                    "description": "Optional: Specific leave type to check (e.g., PTO, Sick Leave)"
                }
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "calculate_eligibility",
        "description": "Calculate if an employee is eligible for leave based on balance, policy rules, and dates. Use this when the user asks if they can take leave or wants to request leave.",
        "function": calculate_eligibility,
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID"
                },
                "leave_type": {
                    "type": "string",
                    "description": "Type of leave (e.g., PTO, Sick Leave)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Leave start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "Leave end date in YYYY-MM-DD format"
                },
                "num_days": {
                    "type": "integer",
                    "description": "Number of days requested"
                }
            },
            "required": ["employee_id", "leave_type", "start_date", "end_date", "num_days"]
        }
    },
    {
        "name": "get_leave_policy_details",
        "description": "Get detailed leave policy information for a country and leave type. Use this when the user asks about leave policies, rules, or allowances.",
        "function": get_leave_policy_details,
        "parameters": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "Country code (US, India, UK)"
                },
                "leave_type": {
                    "type": "string",
                    "description": "Optional: Specific leave type"
                }
            },
            "required": ["country"]
        }
    }
]
