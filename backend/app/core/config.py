from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IESL Man Management API"
    app_env: str = "development"

    docs_enabled: bool = True
    docs_url: str = "/api-docs"
    redoc_url: str = "/api-redoc"
    openapi_url: str = "/api/v1/openapi.json"
    api_key_header_name: str = "x-api-key"

    db_server: str = "localhost"
    db_port: int = 1433
    db_name: str = "IESLManManagement"
    db_user: str = "sa"
    db_password: str = "YourStrongPassword!"
    db_driver: str = "ODBC Driver 18 for SQL Server"

    tez_erp_base_url: str = "https://example-tez.local/api"
    tez_employee_endpoint: str = "employeeget"
    tez_erp_api_key: str = ""
    tez_timeout_seconds: int = 30
    tez_max_retries: int = 3
    working_hours_per_month: int = 160
    tez_company_endpoint: str = "companyget"
    tez_branch_endpoint: str = "branchget"
    tez_department_endpoint: str = "departmentget"
    tez_customer_endpoint: str = "customerget"
    tez_workflow_endpoint: str = "workflowget"
    tez_project_endpoint: str = "projectget"
    tez_cost_center_endpoint: str = "costcenterget"
    strict_master_validation: bool = True
    ticket_api_base_url: str = "https://beta.tezerp.com/API/AppScript.aspx"
    ticket_api_key: str = ""
    ticket_api_auth_mode: str = "api_key"
    ticket_api_key_header: str = "x-api-key"
    ticket_api_timeout_seconds: int = 30
    ticket_api_max_retries: int = 3
    ticket_api_mock_mode: bool = True
    ticket_api_ticket_endpoint: str = "tickets"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_database_uri(self) -> str:
        driver = self.db_driver.replace(" ", "+")
        return (
            f"mssql+pyodbc://{self.db_user}:{self.db_password}@"
            f"{self.db_server}:{self.db_port}/{self.db_name}?driver={driver}&TrustServerCertificate=yes"
        )


settings = Settings()
