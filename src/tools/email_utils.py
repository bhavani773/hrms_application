import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def send_email(to_email: str, subject: str, body: str, template_id: Optional[str] = None, dynamic_data: Optional[dict] = None) -> int:
    """Send email via SMTP"""
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL]):
        print(f"Warning: SMTP configuration incomplete, simulating email to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return 202  # Simulate success for testing
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable TLS encryption
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return 200
        
    except Exception as e:
        print(f"Email send failed: {e}")
        return 500

def send_admin_email(subject: str, body: str) -> list[int]:
    """Send email to all admin recipients"""
    admin_emails = os.getenv("ADMIN_EMAILS", "hr-team@company.com").split(",")
    results = []
    for email in admin_emails:
        email = email.strip()
        if email:
            status = send_email(email, subject, body)
            results.append(status)
    return results