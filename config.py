"""
Configuration module for loading environment variables and API credentials.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Claude API (Anthropic library uses ANTHROPIC_API_KEY by default)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Naver Maps API
    NAVER_MAPS_CLIENT_ID = os.getenv("NAVER_MAPS_CLIENT_ID")
    NAVER_MAPS_CLIENT_SECRET = os.getenv("NAVER_MAPS_CLIENT_SECRET")

    # Google Sheets API
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH",
        "./credentials.json"
    )

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that all required API keys are set.

        Returns:
            List of missing configuration keys.
        """
        missing = []

        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")

        if not cls.NAVER_MAPS_CLIENT_ID:
            missing.append("NAVER_MAPS_CLIENT_ID")

        if not cls.NAVER_MAPS_CLIENT_SECRET:
            missing.append("NAVER_MAPS_CLIENT_SECRET")

        # Google Sheets is optional - don't block if not configured
        # if not Path(cls.GOOGLE_SHEETS_CREDENTIALS_PATH).exists():
        #     missing.append(f"Google Sheets credentials file at {cls.GOOGLE_SHEETS_CREDENTIALS_PATH}")

        return missing

    @classmethod
    def is_google_sheets_configured(cls) -> bool:
        """Check if Google Sheets API is configured."""
        return Path(cls.GOOGLE_SHEETS_CREDENTIALS_PATH).exists()
