"""
tests/test_email.py — Tests for email sending via EmailService

This module contains integration tests for the EmailService.send_user_email method,
ensuring markdown-based templates are sent correctly.
"""

import os
import sys
import pytest
# Allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.mark.asyncio
async def test_send_markdown_email(email_service):
    """Test that send_user_email successfully sends a markdown email using the 'email_verification' template."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "verification_url": "http://example.com/verify?token=abc123"
    }
    await email_service.send_user_email(user_data, 'email_verification')
    # Manual verification in Mailtrap...
