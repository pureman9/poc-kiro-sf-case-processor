"""Configuration loader — reads environment variables via python-dotenv."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""
    # Salesforce
    sf_username: str
    sf_password: str
    sf_security_token: str
    sf_domain: str

    # Customer Data Store
    customer_data_path: str

    # Logging
    log_level: str

    # Mobius API (optional)
    mobius_api_url: str | None
    mobius_api_key: str | None
    mobius_timeout: int

    # Jira (optional)
    jira_base_url: str | None
    jira_api_token: str | None
    jira_project_key: str | None
    jira_test_plan_key: str | None


def load_config() -> AppConfig:
    """Load configuration from .env file and environment variables.

    Raises:
        ValueError: If required Salesforce environment variables are missing.
    """
    load_dotenv()

    # Required Salesforce vars
    sf_username = os.getenv("SF_USERNAME", "")
    sf_password = os.getenv("SF_PASSWORD", "")
    sf_security_token = os.getenv("SF_SECURITY_TOKEN", "")
    sf_domain = os.getenv("SF_DOMAIN", "login")

    if not sf_username or not sf_password:
        raise ValueError(
            "Missing required Salesforce environment variables. "
            "Set SF_USERNAME and SF_PASSWORD in .env file."
        )

    return AppConfig(
        sf_username=sf_username,
        sf_password=sf_password,
        sf_security_token=sf_security_token,
        sf_domain=sf_domain,
        customer_data_path=os.getenv("CUSTOMER_DATA_PATH", "./data/customer_data.json"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        mobius_api_url=os.getenv("MOBIUS_API_URL") or None,
        mobius_api_key=os.getenv("MOBIUS_API_KEY") or None,
        mobius_timeout=int(os.getenv("MOBIUS_TIMEOUT", "30")),
        jira_base_url=os.getenv("JIRA_BASE_URL") or None,
        jira_api_token=os.getenv("JIRA_API_TOKEN") or None,
        jira_project_key=os.getenv("JIRA_PROJECT_KEY") or None,
        jira_test_plan_key=os.getenv("JIRA_TEST_PLAN_KEY") or None,
    )
