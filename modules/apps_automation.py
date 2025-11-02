"""Small helpers for messaging and email automation."""

def send_whatsapp_message(recipient_name, message):
    """Send a WhatsApp message via pywhatkit to a contact in modules/contacts.py.

    Parameters:
    - recipient_name: Key in `modules/contacts.contacts` mapping to a phone number.
    - message: The content to send.

    Returns:
    - A human-friendly status string.
    """
    try:
        import pywhatkit as kit
    except ImportError:
        return "Failed to import pywhatkit. Please install it with 'pip install pywhatkit'."
    try:
        from modules import contacts
    except ImportError:
        return "Failed to import contacts. Please ensure 'modules/contacts.py' exists and is correct."

    # Get the recipient's phone number from the contacts
    recipient_number = contacts.get(recipient_name)
    if not recipient_number:
        return f"Contact '{recipient_name}' not found. Please check your contacts."
    try:
        kit.sendwhatmsg_instantly(recipient_number, message, wait_time=10, tab_close=True)
        return "The message was sent successfully!"
    except Exception as e:
        return f"Failed to send the message: {e}"

def send_email(subject, body, to_email):
    """Send a simple plaintext email using SMTP credentials from environment."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    from dotenv import load_dotenv

    load_dotenv()  # Load environment variables from .env file

    if not all([subject, body, to_email]):
        return "Error: Subject, body, and recipient email are required."

    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    if not from_email or not password:
        return "Error: Email credentials not found in environment variables.  Please set EMAIL_ADDRESS and EMAIL_PASSWORD."

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        return "Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        return "Error: Email authentication failed. Please check your credentials."
    except smtplib.SMTPException as e:
        return f"SMTP error occurred: {str(e)}"
    except TimeoutError:
        return "Error: Connection timed out while sending email."
    except Exception as e:
        return f"Error sending email: {str(e)}"
