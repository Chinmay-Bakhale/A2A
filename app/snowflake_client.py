"""
Snowflake client with circuit breaker pattern
In production, this connects to actual Snowflake warehouse
For this assignment, we'll use mock data with circuit breaker pattern
"""

import logging
from typing import Dict, Any, Optional, List
from app.circuit_breaker import circuit_breaker
from app.mock_data import get_employee_by_id, get_employee_by_email, EMPLOYEE_DATA

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """
    Snowflake client wrapper with resilience patterns
    In production, uses snowflake-snowpark-python
    """
    
    def __init__(
        self,
        account: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None
    ):
        """
        Initialize Snowflake client
        
        In production, these would be real credentials
        For this assignment, we use mock data
        """
        self.account = account
        self.user = user
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        
        # Connection status
        self.connected = False
        
        logger.info(f"SnowflakeClient initialized (mock mode)")
    
    @circuit_breaker(
        failure_threshold=3,
        timeout=30,
        expected_exception=Exception,
        name="snowflake_connection"
    )
    def connect(self) -> bool:
        """
        Establish connection to Snowflake
        Protected by circuit breaker
        
        Returns:
            True if connected successfully
        """
        try:
            # In production:
            # from snowflake.snowpark import Session
            # self.session = Session.builder.configs({...}).create()
            
            logger.info("Connecting to Snowflake (mock)")
            
            # Simulate connection
            self.connected = True
            logger.info("Connected to Snowflake successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            self.connected = False
            raise
    
    @circuit_breaker(
        failure_threshold=5,
        timeout=60,
        expected_exception=Exception,
        name="snowflake_query_employee"
    )
    def query_employee_data(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Query employee data from Snowflake
        Protected by circuit breaker
        
        Args:
            employee_id: Employee ID to query
            
        Returns:
            Employee data dictionary or None
        """
        try:
            if not self.connected:
                self.connect()
            
            logger.info(f"Querying employee data for {employee_id}")
            
            # In production, this would be a real Snowflake query:
            # sql = f"SELECT * FROM employees WHERE employee_id = '{employee_id}'"
            # result = self.session.sql(sql).collect()
            
            # For this assignment, use mock data
            employee = get_employee_by_id(employee_id)
            
            if employee:
                logger.info(f"Employee data retrieved for {employee_id}")
            else:
                logger.warning(f"No employee found with ID {employee_id}")
            
            return employee
            
        except Exception as e:
            logger.error(f"Error querying employee data: {str(e)}")
            raise
    
    @circuit_breaker(
        failure_threshold=5,
        timeout=60,
        expected_exception=Exception,
        name="snowflake_query_employees_by_dept"
    )
    def query_employees_by_department(self, department: str) -> List[Dict[str, Any]]:
        """
        Query all employees in a department
        Protected by circuit breaker
        
        Args:
            department: Department name
            
        Returns:
            List of employee dictionaries
        """
        try:
            if not self.connected:
                self.connect()
            
            logger.info(f"Querying employees in department: {department}")
            
            # In production:
            # sql = f"SELECT * FROM employees WHERE department = '{department}'"
            # result = self.session.sql(sql).collect()
            
            # Mock data filter
            employees = [
                emp for emp in EMPLOYEE_DATA.values()
                if emp["department"].lower() == department.lower()
            ]
            
            logger.info(f"Found {len(employees)} employees in {department}")
            return employees
            
        except Exception as e:
            logger.error(f"Error querying employees by department: {str(e)}")
            raise
    
    @circuit_breaker(
        failure_threshold=5,
        timeout=60,
        expected_exception=Exception,
        name="snowflake_update_leave_balance"
    )
    def update_leave_balance(
        self,
        employee_id: str,
        leave_type: str,
        days_to_deduct: int
    ) -> bool:
        """
        Update employee leave balance after approval
        Protected by circuit breaker
        
        Args:
            employee_id: Employee ID
            leave_type: Type of leave
            days_to_deduct: Number of days to deduct
            
        Returns:
            True if successful
        """
        try:
            if not self.connected:
                self.connect()
            
            logger.info(
                f"Updating leave balance for {employee_id}: "
                f"{leave_type} -{days_to_deduct} days"
            )
            
            # In production:
            # sql = f"""
            # UPDATE employee_leave_balances
            # SET remaining = remaining - {days_to_deduct}
            # WHERE employee_id = '{employee_id}' AND leave_type = '{leave_type}'
            # """
            # self.session.sql(sql).collect()
            
            # Mock update (in-memory)
            employee = get_employee_by_id(employee_id)
            if employee and leave_type in employee["leave_balances"]:
                current = employee["leave_balances"][leave_type]["remaining"]
                employee["leave_balances"][leave_type]["remaining"] = current - days_to_deduct
                employee["leave_balances"][leave_type]["used"] += days_to_deduct
                logger.info("Leave balance updated successfully")
                return True
            
            logger.warning(f"Could not update balance for {employee_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating leave balance: {str(e)}")
            raise
    
    def close(self):
        """Close Snowflake connection"""
        try:
            # In production:
            # self.session.close()
            
            self.connected = False
            logger.info("Snowflake connection closed")
            
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and circuit breaker states"""
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


# Global client instance (singleton pattern)
_snowflake_client: Optional[SnowflakeClient] = None


def get_snowflake_client() -> SnowflakeClient:
    """
    Get or create Snowflake client singleton
    
    Returns:
        SnowflakeClient instance
    """
    global _snowflake_client
    
    if _snowflake_client is None:
        # In production, load from environment variables
        _snowflake_client = SnowflakeClient()
        _snowflake_client.connect()
    
    return _snowflake_client
