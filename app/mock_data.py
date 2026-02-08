"""
Mock data for Leave Policy Assistant
In production, this would come from Snowflake/database
"""

from datetime import datetime
from typing import Dict, Any

# Leave Policies by Country
LEAVE_POLICIES: Dict[str, Dict[str, Any]] = {
    "US": {
        "PTO": {
            "annual_allowance": 20,
            "carryover_limit": 5,
            "min_notice_days": 3,
            "max_consecutive_days": 10,
            "blackout_periods": ["Dec 20-31"],
            "approval_required": True,
            "description": "Paid Time Off for vacation, personal needs"
        },
        "Sick Leave": {
            "annual_allowance": 10,
            "carryover_limit": 0,
            "min_notice_days": 0,
            "documentation_required_after_days": 3,
            "description": "Leave for illness or medical appointments"
        },
        "Parental Leave": {
            "allowance_weeks": 16,
            "eligibility_months": 12,
            "paid": True,
            "description": "Leave for new parents (birth or adoption)"
        }
    },
    "India": {
        "Privilege Leave": {
            "annual_allowance": 18,
            "carryover_limit": 30,
            "min_notice_days": 7,
            "encashment_allowed": True,
            "description": "Earned leave that can be planned in advance"
        },
        "Casual Leave": {
            "annual_allowance": 12,
            "carryover_limit": 0,
            "max_consecutive_days": 3,
            "description": "Short-term unplanned leave for personal matters"
        },
        "Sick Leave": {
            "annual_allowance": 12,
            "carryover_limit": 0,
            "documentation_required_after_days": 2,
            "description": "Leave for illness or medical emergencies"
        },
        "Optional Holidays": {
            "annual_allowance": 3,
            "from_list": True,
            "advance_booking_required": True,
            "description": "Choose from a list of festival/cultural holidays"
        },
        "Maternity Leave": {
            "allowance_weeks": 26,
            "paid": True,
            "description": "Leave for mothers before and after childbirth"
        },
        "Paternity Leave": {
            "allowance_weeks": 2,
            "paid": True,
            "description": "Leave for fathers after childbirth"
        }
    },
    "UK": {
        "Annual Leave": {
            "annual_allowance": 25,
            "carryover_limit": 5,
            "min_notice_days": 14,
            "description": "Statutory annual leave entitlement"
        },
        "Sick Leave": {
            "annual_allowance": 15,
            "paid_days": 10,
            "documentation_required_after_days": 7,
            "description": "Leave for illness with partial pay"
        }
    }
}

# Mock Employee Data
EMPLOYEE_DATA: Dict[str, Dict[str, Any]] = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "John Doe",
        "email": "john.doe@company.com",
        "country": "US",
        "department": "Engineering",
        "hire_date": "2022-01-15",
        "leave_balances": {
            "PTO": {"total": 20, "used": 8, "remaining": 12},
            "Sick Leave": {"total": 10, "used": 2, "remaining": 8},
            "Parental Leave": {"total": 16, "used": 0, "remaining": 16}
        },
        "pending_requests": []
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Priya Sharma",
        "email": "priya.sharma@company.com",
        "country": "India",
        "department": "Product",
        "hire_date": "2021-06-20",
        "leave_balances": {
            "Privilege Leave": {"total": 18, "used": 5, "remaining": 13},
            "Casual Leave": {"total": 12, "used": 7, "remaining": 5},
            "Sick Leave": {"total": 12, "used": 3, "remaining": 9},
            "Optional Holidays": {"total": 3, "used": 1, "remaining": 2}
        },
        "pending_requests": [
            {
                "leave_type": "Privilege Leave",
                "start_date": "2024-03-15",
                "end_date": "2024-03-20",
                "status": "pending"
            }
        ]
    },
    "EMP003": {
        "employee_id": "EMP003",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "country": "UK",
        "department": "Marketing",
        "hire_date": "2023-03-10",
        "leave_balances": {
            "Annual Leave": {"total": 25, "used": 10, "remaining": 15},
            "Sick Leave": {"total": 15, "used": 0, "remaining": 15}
        },
        "pending_requests": []
    },
    "EMP004": {
        "employee_id": "EMP004",
        "name": "Raj Patel",
        "email": "raj.patel@company.com",
        "country": "India",
        "department": "Engineering",
        "hire_date": "2020-09-01",
        "leave_balances": {
            "Privilege Leave": {"total": 18, "used": 12, "remaining": 6},
            "Casual Leave": {"total": 12, "used": 9, "remaining": 3},
            "Sick Leave": {"total": 12, "used": 5, "remaining": 7},
            "Optional Holidays": {"total": 3, "used": 3, "remaining": 0}
        },
        "pending_requests": []
    }
}


def get_employee_by_id(employee_id: str) -> Dict[str, Any] | None:
    """Retrieve employee data by ID"""
    return EMPLOYEE_DATA.get(employee_id)


def get_employee_by_email(email: str) -> Dict[str, Any] | None:
    """Retrieve employee data by email"""
    for emp in EMPLOYEE_DATA.values():
        if emp["email"].lower() == email.lower():
            return emp
    return None


def get_leave_policy(country: str, leave_type: str) -> Dict[str, Any] | None:
    """Retrieve leave policy for a specific country and leave type"""
    country_policies = LEAVE_POLICIES.get(country)
    if not country_policies:
        return None
    return country_policies.get(leave_type)


def get_all_leave_types(country: str) -> list[str]:
    """Get all available leave types for a country"""
    country_policies = LEAVE_POLICIES.get(country, {})
    return list(country_policies.keys())