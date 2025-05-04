"""Client app for email routing"""
# pylint: disable=logging-fstring-interpolation

import logging
import smtplib
from builtins import Exception, int, str
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from settings.config import settings


class SMTPClient:
    """SMTP Client declaration"""
    def __init__(self, server: str, port: int, username: str, password: str):
        self.server = server
        self.port = port
        self.username = username
        self.password = password

    def send_email(self, subject: str, html_content: str, recipient: str):
        """Auto send email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.username
            message["To"] = recipient
            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()  # Use TLS
                server.login(self.username, self.password)
                server.sendmail(self.username, recipient, message.as_string())
            logging.info(f"Email sent to {recipient}")
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise
