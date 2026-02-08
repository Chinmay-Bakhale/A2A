import logging
from typing import Dict, Any, Optional, List
from app.circuit_breaker import circuit_breaker
from app.mock_data import get_employee_by_id, get_employee_by_email, EMPLOYEE_DATA

logger = logging.getLogger(__name__)


class SnowflakeClient:
    def __init__(self, account: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None,
                 warehouse: Optional[str] = None, database: Optional[str] = None, schema: Optional[str] = None):
        self.account = account
        self.user = user
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.connected = False
    
    @circuit_breaker(failure_threshold=3, timeout=30, expected_exception=Exception, name="snowflake_connection")
    def connect(self) -> bool:
        self.connected = True
        return True
    
    @circuit_breaker(failure_threshold=5, timeout=60, expected_exception=Exception, name="snowflake_query_employee")
    def query_employee_data(self, employee_id: str) -> Optional[Dict[str, Any]]:
        if not self.connected:
            self.connect()
        return get_employee_by_id(employee_id)
    
    @circuit_breaker(failure_threshold=5, timeout=60, expected_exception=Exception, name="snowflake_query_employees_by_dept")
    def query_employees_by_department(self, department: str) -> List[Dict[str, Any]]:
        if not self.connected:
            self.connect()
        return [emp for emp in EMPLOYEE_DATA.values() if emp["department"].lower() == department.lower()]
    
    @circuit_breaker(failure_threshold=5, timeout=60, expected_exception=Exception, name="snowflake_update_leave_balance")
    def update_leave_balance(self, employee_id: str, leave_type: str, days_to_deduct: int) -> bool:
        if not self.connected:
            self.connect()
        
        employee = get_employee_by_id(employee_id)
        if employee and leave_type in employee["leave_balances"]:
            current = employee["leave_balances"][leave_type]["remaining"]
            employee["leave_balances"][leave_type]["remaining"] = current - days_to_deduct
            employee["leave_balances"][leave_type]["used"] += days_to_deduct
            return True
        return False
    
    def close(self):
        self.connected = False
    
    def get_connection_status(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "account": self.account,
            "warehouse": self.warehouse,
            "database": self.database,
            "circuit_breakers": {
                "connection": getattr(
                    self.connect, 'circuit_breaker', None
                ).get_state() if hasattr(self.connect, 'circuit_breaker') else None,
                "query_employee": getattr(
                    self.query_employee_data, 'circuit_breaker', None
                ).get_state() if hasattr(self.query_employee_data, 'circuit_breaker') else None
            }
        }


_snowflake_client: Optional[SnowflakeClient] = None


def get_snowflake_client() -> SnowflakeClient:
    global _snowflake_client
    if _snowflake_client is None:
        _snowflake_client = SnowflakeClient()
        _snowflake_client.connect()
    return _snowflake_client
