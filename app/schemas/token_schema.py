"""File to define token schema"""
from builtins import str

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Declaring function return for token"""
    access_token: str
    token_type: str = "bearer"

    class Config:
        """Configuration class"""
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lQGV4YW1wbGUuY29tIiwicm9sZSI6IkFVVEhFTlRJQ0FURUQiLCJleHAiOjE2MjQzMzQ5ODR9.ZGNjNjI2ZjI4MmYzNTk0MjVjNDk0ZjI4MjdjNGEzNmI1",
                "token_type": "bearer",
            }
        }
