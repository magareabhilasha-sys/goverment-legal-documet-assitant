import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD

logger = logging.getLogger("email_service")

def send_reset_password_email(to_email: str, reset_token: str):
    """
    Sends a real password reset email using the configured SMTP server.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.error("SMTP_EMAIL or SMTP_PASSWORD not set. Cannot send email.")
        return False
        
    # Using relative link or env var in production.
    # For now assuming Vite default localhost for local dev.
    frontend_url = "http://localhost:5173" 
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Password Reset Request - AI Legal Assistant"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    
    text = f"You requested a password reset. Click the link below to reset your password:\n{reset_link}\nIf you didn't request this, ignore this email."
    html = f"""
    <html>
      <body>
        <h2>Password Reset Request</h2>
        <p>You requested a password reset. Click the link below to reset your password:</p>
        <p><a href="{reset_link}">Reset My Password</a></p>
        <p>If you didn't request this, please ignore this email.</p>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
