def send_whatsapp_message(recipient_name, message):
    """
    Sends a WhatsApp message using pywhatkit, handling the import dynamically.
    
    :param recipient: The phone number to send the message to (string format with country code).
    :param message: The content of the message to send.
    :return: Success or error message as a string.
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

# Example usage:
# if __name__ == "__main__":
#     recipient_name = "mama"
#     message_content = f"The 71 - 32 is: {71 - 32}"
#     result = send_whatsapp_message(recipient_name, message_content)
#     print(result)
